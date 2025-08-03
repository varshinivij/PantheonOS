.. Pantheon Agents documentation master file

Welcome to Pantheon
===================

.. image:: https://github.com/aristoteleo/pantheon-agents/actions/workflows/test.yml/badge.svg
   :target: https://github.com/aristoteleo/pantheon-agents/actions/workflows/test.yml
   :alt: Build Status

.. image:: https://img.shields.io/pypi/v/pantheon-agents.svg
   :target: https://pypi.org/project/pantheon-agents/
   :alt: PyPI Version

.. image:: https://img.shields.io/github/license/aristoteleo/pantheon-agents
   :target: https://github.com/aristoteleo/pantheon-agents/blob/master/LICENSE
   :alt: License

**Pantheon** is a framework for building distributed LLM-based multi-agent systems.

**Work In Progress** - This project is actively under development.

Key Features
------------

.. grid:: 1 2 2 3
   :gutter: 3

   .. grid-item::

      **🤖 Multiple Agent Types**
      
      Sequential, Swarm, and MoA (Mixture-of-Agents) team collaboration patterns.

   .. grid-item::

      **🛠️ Built-in Toolsets**
      
      Python, R, Shell, and Web browsing capabilities for agents.

   .. grid-item::

      **🧠 Memory Persistence**
      
      Maintain context and state across agent conversations.

   .. grid-item::

      **💬 ChatRoom Service**
      
      Interactive chat interface with Web UI support.

   .. grid-item::

      **🚀 Distributed Support**
      
      Run tools and agents across multiple machines.

   .. grid-item::

      **🎯 Reasoning Models**
      
      Support for O1, Gemini Flash Thinking, and Deepseek-R1.

Quick Start
-----------

Install from PyPI:

.. code-block:: bash

   pip install pantheon-agents

Start a ChatRoom:

.. code-block:: bash

   export OPENAI_API_KEY=your_openai_api_key
   python -m pantheon.chatroom

Then connect via the Web UI at https://pantheon-ui.vercel.app/

Simple Agent Example
--------------------

.. code-block:: python

   import asyncio
   from pantheon.agent import Agent

   # Create a simple agent
   agent = Agent(
       name="assistant",
       instructions="You are a helpful assistant.",
       model="gpt-4o-mini"
   )

   # Chat with the agent
   asyncio.run(agent.chat())

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Home

   overview
   highlights
   architecture

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Quick Start

   installation
   quickstart

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Concepts

   concepts/index
   concepts/agent
   concepts/team
   concepts/memory
   concepts/toolset
   concepts/endpoint
   concepts/chatroom

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Agent

   agent/index
   agent/agent_api
   agent/smart_func_api
   agent/remote_agent

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Team

   team/index
   team/sequential_team
   team/moa_team
   team/swarm_team
   team/swarm_center_team
   team/pantheon_team

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Toolsets

   toolsets/index
   toolsets/python_interpreter
   toolsets/r_interpreter
   toolsets/shell
   toolsets/web_browse
   toolsets/scraper_api
   toolsets/file_editor
   toolsets/vector_rag
   toolsets/rag_system

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Endpoint and Chatroom

   endpoint_chatroom/index
   endpoint_chatroom/architecture

.. toctree::
   :hidden:
   :maxdepth: 1
   :caption: Contribution Guide

   contributing

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Additional Resources

   api/index
   guides/index
   examples/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`