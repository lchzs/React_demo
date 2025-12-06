# Project Name

## Environment Installation

To set up the environment and install the required dependencies, please run the following commands:

```bash
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## Configuration
This project supports two operation modes, which can be configured in the config.py file:

- Evaluate Mode
- Debug Mode

Please refer to config.py for detailed configuration options.

## Frontend Demo
The project includes a web-based demo powered by Streamlit. To launch it, run:
```bash
streamlit run app.py
```
Note: When running the Streamlit demo, the Debug Mode automatically transforms into a Conversational (Chat) Mode.