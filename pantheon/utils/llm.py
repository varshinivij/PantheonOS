def import_litellm():
    import warnings
    warnings.filterwarnings("ignore")
    import litellm
    litellm.suppress_debug_info = True
    return litellm


litellm = import_litellm()
