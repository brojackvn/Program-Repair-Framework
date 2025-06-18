# RegRepair: Prompt-based Automated Program Repair for Regression Bugs

This project provides several shell scripts to run Automated Program Repair (APR) using prompts and conversational approaches.

## 🔧 Setup

### 1. Set the OpenAI API Key
The `.env` file is already created. Please ensure it includes your OpenAI API key.

### 2. Install Dependencies

Install the required Python packages using:

```bash
pip install -r requirements.txt
```

## 🚀 Running the Tools

### 3.1 Run Prompt-based APR without BIC

```bash
bash prompt_apr.sh
```

### 3.2 Run Conversational APR without BIC

```bash
bash conversational_apr.sh
```

### 3.3 Run Prompt-based APR with BIC

```bash
bash prompt_apr_with_bic.sh
```

### 3.4 Run Conversational APR with BIC

```bash
bash conversational_apr_with_bic.sh
```