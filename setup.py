#!/usr/bin/env python3
"""
Setup script for Personalized Travel Itinerary Generator
Handles virtual environment creation and dependency installation
"""

import os
import subprocess
import sys
from pathlib import Path

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    
    if not venv_path.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created successfully!")
    else:
        print("✅ Virtual environment already exists.")
    
    return venv_path

def get_activation_command():
    """Get the appropriate activation command for the current OS."""
    if os.name == 'nt':  # Windows
        return str(Path("venv") / "Scripts" / "activate.bat")
    else:  # Unix/macOS
        return f"source {Path('venv') / 'bin' / 'activate'}"

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies from requirements.txt...")
    
    # Use the python executable from the virtual environment
    if os.name == 'nt':  # Windows
        python_exe = Path("venv") / "Scripts" / "python.exe"
    else:  # Unix/macOS
        python_exe = Path("venv") / "bin" / "python"
    
    subprocess.run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(python_exe), "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    print("✅ Dependencies installed successfully!")

def create_project_structure():
    """Create the project directory structure."""
    directories = [
        "src",
        "src/agents",
        "src/tools", 
        "src/workflows",
        "tests",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files for Python packages
        if directory.startswith("src"):
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    print("✅ Project structure created successfully!")

def create_env_file():
    """Create .env file from .env.example if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            # Copy .env.example to .env
            env_file.write_text(env_example.read_text())
            print("✅ .env file created from .env.example")
            print("⚠️  Please update .env with your actual Google API key!")
        else:
            # Create basic .env file
            env_content = """# Google API Key for Gemini integration
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Set to development for verbose logging
ENVIRONMENT=development
"""
            env_file.write_text(env_content)
            print("✅ .env file created")
            print("⚠️  Please update .env with your actual Google API key!")
    else:
        print("✅ .env file already exists")

def main():
    """Main setup function."""
    print("🚀 Setting up Personalized Travel Itinerary Generator...")
    print("=" * 60)
    
    try:
        # Check Python version
        if sys.version_info < (3, 12):
            print("❌ Error: Python 3.12 or higher is required!")
            print(f"Current version: {sys.version}")
            sys.exit(1)
        
        print(f"✅ Python version: {sys.version}")
        
        # Setup steps
        venv_path = create_virtual_environment()
        install_dependencies()
        create_project_structure()
        create_env_file()
        
        print("\n" + "=" * 60)
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print(f"1. Activate virtual environment: {get_activation_command()}")
        print("2. Update .env file with your Google API key")
        print("3. Run: python -c 'import google_adk; print(\"Google ADK imported successfully!\")' to test")
        print("\n💡 You're ready to start development!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during setup: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()