import io
import os
import ast
import base64
import traceback
from contextlib import redirect_stdout, redirect_stderr

from executor.engine import ProcessJob
from magique.ai.tools.python.python_interpreter import (
    PythonInterpreterToolSet,
    PythonInterpreterError,
)
from magique.ai.toolset import tool


def exec_with_echo(code, env=None):
    if env is None:
        env = {}
    tree = ast.parse(code)
    for node in tree.body:
        if isinstance(node, ast.Expr):
            expr_code = compile(ast.Expression(node.value), '<string>', 'eval')
            result = eval(expr_code, env)
            print(result)
        else:
            exec(compile(ast.Module([node], []), '<string>', 'exec'), env)


class ScientificPythonInterpreterToolSet(PythonInterpreterToolSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_code = """try:
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import os
    import uuid

    GLOBAL_FIG_PATH = None
    GLOBAL_FIG_DIR = ".matplotlib_figs"

    original_show = plt.show

    def __custom_plt_show(*args, **kwargs):
        global GLOBAL_FIG_PATH
        fig = plt.gcf()
        if not fig.get_axes():
            print("No active figure to save.")
            plt.close(fig)
            return

        fig_uuid = str(uuid.uuid4())
        os.makedirs(GLOBAL_FIG_DIR, exist_ok=True)
        GLOBAL_FIG_PATH = os.path.join(GLOBAL_FIG_DIR, fig_uuid + ".png")
        fig.savefig(GLOBAL_FIG_PATH, format='png')
        plt.close(fig)

    __plt_show = plt.show
    plt.show = __custom_plt_show
except Exception as e:
    print(f"Error in matplotlib initialization: {e}")
"""

    @tool
    async def run_code_in_interpreter(
            self,
            code: str,
            interpreter_id: str,
            result_var_name: str | None = None,
            ) -> dict:
        """Run code in an interpreter.

        Args:
            code: The code to run.
            interpreter_id: The id of the interpreter to run the code in.
            result_var_name: The name of the variable you want to get the result from.
                If not needed, set to None. Default is None.

        Returns:
            A dictionary with the result, stdout, and stderr.
        """
        code = "GLOBAL_FIG_PATH = None\n" + code
        res = await super().run_code_in_interpreter(
            code,
            interpreter_id,
            result_var_name,
        )
        res2 = await super().run_code_in_interpreter(
            "None",
            interpreter_id,
            "GLOBAL_FIG_PATH",
        )
        fig_path = res2["result"]
        if fig_path is not None:
            res["fig_storage_path"] = fig_path
            open_path = fig_path
            if self.workdir:
                open_path = os.path.join(self.workdir, fig_path)
            with open(open_path, "rb") as f:
                base64_img = base64.b64encode(f.read()).decode("utf-8")
            base64_uri = f"data:image/png;base64,{base64_img}"
            res["plt_show_base64_uri"] = base64_uri
            res["hidden_to_model"] = ["plt_show_base64_uri"]
        return res

    @tool
    async def new_interpreter(self) -> str:
        """Create a new Python interpreter and return its id.
        You can use `run_code_in_interpreter` to run code in the interpreter,
        by providing the interpreter id. """
        self._init_engine()

        async def interpreter():
            __res = None
            __stdout = io.StringIO()
            __stderr = io.StringIO()
            while True:
                code, var_name = yield __res, __stdout.getvalue(), __stderr.getvalue()
                __stdout.seek(0)
                __stderr.seek(0)
                try:
                    with redirect_stdout(__stdout), redirect_stderr(__stderr):
                        exec_with_echo(code, globals())
                except Exception:
                    traceback_str = traceback.format_exc()
                    __res = PythonInterpreterError(traceback_str)
                    continue
                if var_name is None:
                    __res = None
                else:
                    __res = globals().get(var_name)

        job = ProcessJob(interpreter)
        await self.engine.submit_async(job)
        await job.wait_until_status("running")
        self.jobs[job.id] = job
        g = job.result()
        await g.asend(None)  # Initialize the generator
        self.interpreters[job.id] = g
        if self.workdir is not None:
            await self.run_code_in_interpreter(f"import os; os.chdir('{self.workdir}')", job.id)
        if self.init_code is not None:
            await self.run_code_in_interpreter(self.init_code, job.id)
        return job.id
