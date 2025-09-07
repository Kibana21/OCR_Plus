# LLM Configuration Guide

This document explains how to configure the DSPy Data Extractor to use either Azure OpenAI or regular OpenAI using the centralized configuration system.

## 🔧 Configuration Steps

### 1. Set Up Environment Variables

Create a `.env` file in your project root with the following Azure OpenAI variables:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name_here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### 2. Get Your Azure OpenAI Values

You'll need to obtain these values from your Azure portal:

- **AZURE_OPENAI_API_KEY**: Found in your Azure OpenAI resource under "Keys and Endpoint"
- **AZURE_OPENAI_ENDPOINT**: The endpoint URL for your Azure OpenAI resource
- **AZURE_OPENAI_DEPLOYMENT_NAME**: The name of your deployed model (e.g., "gpt-4o-mini")
- **AZURE_OPENAI_API_VERSION**: The API version (typically "2024-02-15-preview")

### 3. Usage Examples

#### Single File Processing
```bash
# Use Azure OpenAI
python main.py data/report.pdf --azure

# Use regular OpenAI (default)
python main.py data/report.pdf
```

#### Batch Processing
```bash
# Process all files with Azure OpenAI
python batch_processor.py data --azure

# Process all files with regular OpenAI
python batch_processor.py data
```

#### Quick Batch Processing
```bash
# Quick processing with Azure OpenAI
python quick_batch.py data --azure

# Quick processing with regular OpenAI
python quick_batch.py data
```

#### Simple DSPy Example
```bash
# Simple example with Azure OpenAI
python ocr.py --azure

# Simple example with regular OpenAI
python ocr.py
```

## 🔄 Switching Between Providers

The application automatically detects which configuration to use:

- **If `--azure` flag is used**: Looks for Azure OpenAI environment variables
- **If no flag is used**: Uses regular OpenAI configuration

## ✅ Verification

To verify your Azure configuration is working:

1. Set up your `.env` file with Azure variables
2. Run: `python main.py --azure`
3. Look for "🔵 Using Azure OpenAI" in the output

## 🚨 Troubleshooting

### Common Issues

1. **"Azure OpenAI configuration incomplete"**
   - Ensure all 4 Azure environment variables are set
   - Check that variable names match exactly

2. **"Invalid API key"**
   - Verify your Azure API key is correct
   - Ensure the key has proper permissions

3. **"Invalid endpoint"**
   - Check that your endpoint URL is correct
   - Ensure it includes the full path (e.g., `https://resource.openai.azure.com/`)

4. **"Deployment not found"**
   - Verify your deployment name matches exactly
   - Ensure the deployment is active in Azure

### Environment Variable Checklist

- [ ] `AZURE_OPENAI_API_KEY` - Your Azure API key
- [ ] `AZURE_OPENAI_ENDPOINT` - Full endpoint URL
- [ ] `AZURE_OPENAI_DEPLOYMENT_NAME` - Exact deployment name
- [ ] `AZURE_OPENAI_API_VERSION` - API version string

## 📝 Example .env File

```bash
# Regular OpenAI (for comparison)
OPENAI_API_KEY=sk-1234567890abcdef...

# Azure OpenAI
AZURE_OPENAI_API_KEY=1234567890abcdef...
AZURE_OPENAI_ENDPOINT=https://mycompany.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

## 🔗 Related Files

- `llm_config.py` - **Centralized LLM configuration module**
- `data_extractor.py` - Main extractor using centralized config
- `page_by_page_extractor.py` - Page-by-page extraction using centralized config
- `batch_processor.py` - Batch processing using centralized config
- `quick_batch.py` - Quick batch processing using centralized config
- `main.py` - Single file processing using centralized config
- `ocr.py` - Simple DSPy example using centralized config
- `config_example.py` - Examples of using the centralized configuration
- `env_template.txt` - Environment variable template

## 🎯 Benefits of Centralized Configuration

- **Single source of truth** for LLM configuration
- **Consistent setup** across all modules
- **Easy switching** between OpenAI and Azure OpenAI
- **Automatic validation** of environment variables
- **Cleaner code** with less duplication
- **Better error handling** with descriptive messages
