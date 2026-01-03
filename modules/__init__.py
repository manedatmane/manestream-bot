"""
Bot modules - each module provides a set of related commands
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.client import BotClient


def load_modules(bot: "BotClient", enabled_modules: list):
    """
    Load enabled modules
    
    Args:
        bot: The bot client instance
        enabled_modules: List of module names to load
    """
    import importlib
    
    loaded = []
    failed = []
    
    for module_name in enabled_modules:
        try:
            module = importlib.import_module(f"modules.{module_name}")
            
            # Call setup function if exists
            if hasattr(module, "setup"):
                module.setup(bot)
            
            loaded.append(module_name)
            print(f"  ✅ Loaded: {module_name}")
            
        except Exception as e:
            failed.append((module_name, str(e)))
            print(f"  ❌ Failed: {module_name} - {e}")
    
    print(f"\n📦 Modules: {len(loaded)} loaded, {len(failed)} failed")
    
    return loaded, failed


def unload_module(bot: "BotClient", module_name: str) -> bool:
    """
    Unload a module
    
    Args:
        bot: The bot client instance
        module_name: Name of module to unload
        
    Returns:
        True if unloaded successfully
    """
    import importlib
    import sys
    
    full_name = f"modules.{module_name}"
    
    if full_name not in sys.modules:
        return False
    
    module = sys.modules[full_name]
    
    # Call teardown if exists
    if hasattr(module, "teardown"):
        try:
            module.teardown(bot)
        except Exception as e:
            print(f"Teardown error for {module_name}: {e}")
    
    # Unregister commands from this module
    from core.registry import registry
    
    if module_name in registry.modules:
        for cmd_name in list(registry.modules[module_name]):
            registry.unregister(cmd_name)
    
    # Remove from sys.modules
    del sys.modules[full_name]
    
    return True
