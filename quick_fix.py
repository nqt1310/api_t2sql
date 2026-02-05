"""
Quick Fix for Haiku and Small Models
Run this if your model is not generating SQL properly
"""
import os
import sys


def update_env_file(fixes: dict):
    """Update .env file with fixes"""
    env_path = ".env"
    
    if not os.path.exists(env_path):
        print(f"❌ .env file not found at {env_path}")
        return False
    
    # Read current .env
    with open(env_path, "r") as f:
        lines = f.readlines()
    
    # Update or add settings
    updated_keys = set()
    new_lines = []
    
    for line in lines:
        key = line.split("=")[0].strip()
        if key in fixes:
            new_lines.append(f"{key}={fixes[key]}\n")
            updated_keys.add(key)
            print(f"✓ Updated: {key}={fixes[key]}")
        else:
            new_lines.append(line)
    
    # Add missing keys
    for key, value in fixes.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}\n")
            print(f"✓ Added: {key}={value}")
    
    # Write back
    with open(env_path, "w") as f:
        f.writelines(new_lines)
    
    print(f"\n✅ .env file updated successfully")
    return True


def quick_fix_mistral():
    """Quick fix for Mistral model"""
    print("MISTRAL OPTIMIZATION")
    print("="*60)
    
    fixes = {
        "LLM_TEMPERATURE": "0.1",
        "LLM_MAX_TOKENS": "4096",
        "LLM_PROVIDER": "ollama",
        "OLLAMA_MODEL": "mistral-nemo:latest",
    }
    
    print("\nApplying optimized settings for Mistral:")
    print("- Temperature: 0.1 (very low for consistent JSON output)")
    print("- Max tokens: 4096 (plenty for complex queries)")
    print("- Model: mistral-nemo:latest (best Mistral variant)")
    
    if update_env_file(fixes):
        print("\n⚠️  IMPORTANT: Restart your API for changes to take effect:")
        print("   Ctrl+C to stop, then run: python main_mcp.py")
        print("\n💡 TIP: If still having issues, try:")
        print("   ollama pull mistral-nemo:latest")
        return True
    return False


def suggest_mistral_variants():
    """Suggest Mistral model variants"""
    print("\nMISTRAL MODEL VARIANTS:")
    print("="*60)
    
    models = [
        ("mistral-nemo:latest", "Recommended - Best for SQL generation", "Fast, reliable, good at following instructions"),
        ("mistral:latest", "Standard Mistral 7B", "Lighter, faster but less capable"),
        ("mistral-small:latest", "Compact version", "For low-resource systems"),
    ]
    
    print("\nAvailable Mistral models (via Ollama):")
    for i, (name, desc, note) in enumerate(models, 1):
        print(f"\n{i}. {name}")
        print(f"   {desc}")
        print(f"   Note: {note}")
        print(f"   Install: ollama pull {name}")
    
    print("\n💡 RECOMMENDATION: Use mistral-nemo:latest")
    print("   It has the best balance of speed and accuracy for SQL generation")
    
    print("\nTo switch models, update your .env:")
    print("   OLLAMA_MODEL=mistral-nemo:latest")
    print("   LLM_TEMPERATURE=0.1")
    print("   LLM_MAX_TOKENS=4096")


def main():
    """Main menu"""
    print("\n" + "="*60)
    print("MISTRAL MODEL OPTIMIZATION TOOL")
    print("="*60)
    
    print("\nChoose an option:")
    print("1. Apply optimal Mistral settings (RECOMMENDED)")
    print("2. Show Mistral model variants")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        quick_fix_mistral()
    elif choice == "2":
        suggest_mistral_variants()
    elif choice == "3":
        print("Exiting...")
        return
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
