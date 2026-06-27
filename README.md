# SaleSim

## Project Overview

SaleSim is a web app for practising sales conversations against an AI prospect. It uses real-time behavioural classification to help improve the user's selling skills. It displays analytics of their performance afterwards such as interest trajectory, classification breakdown and their dominant behaviour during the conversation. 

## Live Demo

[salesim.app](https://salesim.app)

## Architecture

In this project there are two AI agents.

Agent A: an external LLM (Gemini) that acts as the customer and responds to the practicing salesperson, the user.
Agent B: a finetuned DistilBERT model that takes in each conversation pair and classifies the sample from four categories: OH, WC, FD, or AN.

Agent B takes the conversation pair (customer message + salesperson response) as input, instead of just the salesperson's message alone. This is because the salesperson's
behaviour only makes sense in the context of what they were responding to, giving a more useful classification. Classifying the salesperson's message alone would lose that context.

The vanilla Javascript frontend communicates to a FastAPI backend via REST API calls.

When a new user starts a session, their session ID is stored server side, allowing different users to all use the project at the same time.

Agent B runs locally on the server to avoid a startup latency per-request. Agent A makes an external API call to gemini-3.1-flash-lite.

## ML Pipeline

### Schema Design

Initially I came up with six different classes, the last two were Hedging and Premature Discounting. After reviewing initial samples, there was too much ambiguity and overlap for manual labelling by a human as both Hedging and Premature Discounting suggest retreating from a position, making them almost identical at the turn level. So I reduced the number to four.

The final four classes are as follows:

Objection Handling (OH) - The salesperson addresses a specific concern the prospect raised with a direct, structured response.

Weak Concession (WC) - The salesperson loses control, avoids commitment, or reduces price too quickly.

Feature Dumping (FD) - The salesperson lists off features or specs that had no connection with the customers question or concern.

Anchoring (AN) - The salesperson sets a price for the service/product early in the conversation with confidence.


### Data Generation

Gemini created 2400 synthetic samples of conversation pairs.

12 industry topics were randomly sampled to increase variation and each sample was given one classification type making sure that the four classes were balanced in the final dataset. The labels were deliberately left out of the output.

Each API call was dedicated to a specific category with its definition, positive examples, and negative examples referencing the other categories. This helped prevent cross-category bleed that occurred in an earlier iteration where all six categories were rotated within a single prompt.

### Manual Labelling Decision and the Circularity Problem 

Gemini generated all 2400 conversation pairs but deliberately left out classification labels so that I could manually label all of them.

This was done as relying on Gemini to label its own samples would re-introduce the circularity problem. Its label would reflect its own generation intent instead of a consistent human-defined standard.

Gemini controlled both sides of the sample, meaning it could generate trivially classifiable samples that were not grounded in real sales behaviour. This would have meant during training, Agent B would learn pairs that matched the class exactly, rather than universal actual sales behaviour and conversation dialogue.

To fix this Gemini was given explicit positive and negative examples for each category's definition. This allowed Gemini to generate responses grounded in human defined criteria and also exhibiting the target behaviour as defined by the examples.

### Training and Evaluation

`distilbert-base-uncased` was finetuned as it is lightweight enough for CPU inference on a VPS and well-suited to classification tasks.

The final dataset was shuffled with `seed=42` and split into a 70/15/15 train/val/test split.

The resulting finetuned model scored a 0.991 macro F1 on the held-out test set. This score is likely inflated because the test set comes from the same synthetic distribution as the training data, so the model has not been evaluated on real human conversations. The metric macro F1 was used as it treats each class equally regardless of sample count.

### OOD Detection Mechanism and Threshold Calibration

As the model's F1 score was likely to be inflated, the model's confidence on real inputs could not always be trusted. So, instead of returning just the argmax label, the full softmax distribution is returned instead. This allowed an empirically calibrated threshold of 0.65 to be set on the scores and act as an out-of-distribution mechanism. In distribution samples output highly confident scores such as 0.99, while gibberish inputs score much lower with near-tied classes.

Additionally, inputs under 20 characters are not classified at all, as short inputs do not carry enough signal for meaningful classification.

## Tech Stack

Frontend: Vanilla JS, HTML, CSS

Backend: FastAPI, Python, slowapi

ML: DistilBERT, HuggingFace Transformers, PyTorch, gemini-3.1-flash-lite 

Infrastructure: Hetzner VPS, Nginx, Certbot, systemd, Cloudflare

## Running Locally

**Prerequisites:** Python 3.10+

1. Clone the repository
```bash
   git clone https://github.com/TomHarcus/SaleSim.git
   cd SaleSim
```

2. Create and activate a virtual environment
```bash
   python3 -m venv venv
   source venv/bin/activate
```

3. Install dependencies
```bash
   pip install -r requirements.txt
```

4. Create a `.env` file in the `backend/` directory with your Gemini API key
```bash
GEMINI_API_KEY=your_key_here
```

5. Start the backend
```bash
   cd backend
   uvicorn main:app --reload
```

6. Serve the frontend locally
```bash
cd frontend
python3 -m http.server 5500
```
Then open `http://localhost:5500` in your browser.