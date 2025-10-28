# Tutorial: Building an AI Agent for OpenMRS Administration

## Introduction

This tutorial will guide you through building a specialized AI agent that can administer an OpenMRS EMR instance. By the end, you'll have a lightweight model that understands the OpenMRS REST and FHIR APIs and can execute common administrative tasks like creating appointments, managing schedules, and querying patient data.

**What You'll Learn:**
- How to train small language models for tool use/function calling
- How to generate synthetic training data from API documentation
- How to fine-tune models using LoRA for efficiency
- How to build an agent that executes real API calls safely

**Prerequisites:**
- Python programming experience
- Basic understanding of REST APIs
- Access to an OpenMRS instance (local or development)
- GPU with 16GB+ VRAM (or Google Colab access)
- Familiarity with transformers and PyTorch basics

---

## Phase 1: Understanding the Foundation

### What is Tool Calling?

Tool calling (also called function calling) is when a language model learns to generate structured outputs that specify which external function to call and what parameters to use. The model doesn't execute the function—it produces JSON that tells *your code* what to execute.

**Example Input:**
```
"Schedule an appointment for patient John Doe tomorrow at 2pm"
```

**Model Output:**
```json
{
  "function": "create_appointment",
  "arguments": {
    "patient_name": "John Doe",
    "date": "2024-11-01",
    "time": "14:00",
    "appointment_type": "follow-up"
  }
}
```

Your code then takes this structured output and makes the actual API call to OpenMRS.

### Why Small Models Work for Specialized Tasks

Large models store vast amounts of world knowledge in their parameters. For specialized tasks like OpenMRS administration, you don't need that knowledge—you just need the model to:

1. Understand the available API functions
2. Map natural language to the correct function
3. Extract parameters accurately
4. Handle multi-step workflows

A 2-4B parameter model can excel at this when trained on high-quality, task-specific data.

---

## Phase 2: Setting Up Your Environment

### Install Required Libraries

```bash
# Create a virtual environment
python -m venv openmrs-agent-env
source openmrs-agent-env/bin/activate  # On Windows: openmrs-agent-env\Scripts\activate

# Install core dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install transformers==4.38.0
pip install peft==0.8.2
pip install datasets==2.16.0
pip install accelerate==0.26.0
pip install bitsandbytes==0.42.0
pip install wandb  # For experiment tracking
pip install requests  # For API calls
pip install sentence-transformers  # For tool retrieval
```

### Set Up Project Structure

```bash
mkdir openmrs-agent
cd openmrs-agent
mkdir data models scripts outputs
touch scripts/extract_api_schema.py
touch scripts/generate_training_data.py
touch scripts/train_model.py
touch scripts/agent.py
```

---

## Phase 3: Extracting OpenMRS API Schema

The first step is understanding what functions your agent needs to learn. OpenMRS provides Swagger/OpenAPI documentation that describes all available endpoints.

### Script: Extract API Schema

Create `scripts/extract_api_schema.py`:

```python
import requests
import json
from typing import List, Dict

class OpenMRSSchemaExtractor:
    def __init__(self, base_url: str):
        """
        Initialize with your OpenMRS instance URL.
        Example: http://localhost:8080/openmrs
        """
        self.base_url = base_url
        self.fhir_swagger_url = f"{base_url}/module/fhir/rest/swagger.json"
        
    def fetch_fhir_schema(self) -> Dict:
        """Fetch the FHIR API Swagger documentation"""
        try:
            response = requests.get(self.fhir_swagger_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching schema: {e}")
            return {}
    
    def extract_functions(self, swagger_doc: Dict) -> List[Dict]:
        """
        Extract function definitions from Swagger documentation.
        Each function represents an API endpoint.
        """
        functions = []
        
        paths = swagger_doc.get('paths', {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                    # Create a function definition
                    function = {
                        "name": self._create_function_name(method, path),
                        "description": details.get('summary', '') or details.get('description', ''),
                        "endpoint": path,
                        "method": method.upper(),
                        "parameters": self._extract_parameters(details),
                        "returns": self._extract_returns(details)
                    }
                    functions.append(function)
        
        return functions
    
    def _create_function_name(self, method: str, path: str) -> str:
        """Create a readable function name from method and path"""
        # Example: GET /Patient/{id} -> get_patient_by_id
        clean_path = path.replace('/', '_').replace('{', '').replace('}', '')
        clean_path = clean_path.strip('_')
        return f"{method.lower()}_{clean_path}"
    
    def _extract_parameters(self, details: Dict) -> List[Dict]:
        """Extract parameter information"""
        params = []
        
        # URL parameters
        for param in details.get('parameters', []):
            params.append({
                "name": param.get('name'),
                "type": param.get('type', 'string'),
                "required": param.get('required', False),
                "description": param.get('description', ''),
                "location": param.get('in', 'query')  # query, path, header, body
            })
        
        # Request body parameters (for POST/PUT)
        if 'requestBody' in details:
            body = details['requestBody']
            if 'content' in body:
                for content_type, content in body['content'].items():
                    if 'schema' in content:
                        params.append({
                            "name": "body",
                            "type": "object",
                            "required": body.get('required', True),
                            "description": body.get('description', ''),
                            "location": "body",
                            "schema": content['schema']
                        })
        
        return params
    
    def _extract_returns(self, details: Dict) -> Dict:
        """Extract return value information"""
        responses = details.get('responses', {})
        success_response = responses.get('200', responses.get('201', {}))
        
        return {
            "description": success_response.get('description', ''),
            "type": success_response.get('schema', {}).get('type', 'object')
        }
    
    def save_functions(self, functions: List[Dict], output_path: str):
        """Save extracted functions to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(functions, f, indent=2)
        print(f"Saved {len(functions)} functions to {output_path}")
    
    def create_function_catalog(self) -> List[Dict]:
        """
        Main method: Extract and organize all functions
        """
        print("Fetching OpenMRS FHIR schema...")
        swagger_doc = self.fetch_fhir_schema()
        
        if not swagger_doc:
            raise Exception("Failed to fetch schema")
        
        print("Extracting function definitions...")
        functions = self.extract_functions(swagger_doc)
        
        # Filter and prioritize important functions
        priority_functions = self._prioritize_functions(functions)
        
        return priority_functions
    
    def _prioritize_functions(self, functions: List[Dict]) -> List[Dict]:
        """
        Prioritize functions for training. Focus on common administrative tasks.
        """
        # Priority resources for OpenMRS administration
        priority_resources = [
            'patient', 'appointment', 'practitioner', 
            'schedule', 'location', 'encounter',
            'observation', 'condition', 'medication'
        ]
        
        prioritized = []
        other = []
        
        for func in functions:
            # Check if function involves a priority resource
            is_priority = any(
                resource in func['name'].lower() 
                for resource in priority_resources
            )
            
            if is_priority:
                prioritized.append(func)
            else:
                other.append(func)
        
        # Return priority functions first
        return prioritized + other


# Usage
if __name__ == "__main__":
    # Replace with your OpenMRS instance URL
    extractor = OpenMRSSchemaExtractor("http://localhost:8080/openmrs")
    
    functions = extractor.create_function_catalog()
    extractor.save_functions(functions, "data/openmrs_functions.json")
    
    # Print summary
    print(f"\nExtracted {len(functions)} functions")
    print("\nSample functions:")
    for func in functions[:5]:
        print(f"  - {func['name']}: {func['description'][:60]}...")
```

**Run the script:**

```bash
python scripts/extract_api_schema.py
```

This creates `data/openmrs_functions.json` containing all available API functions.

---

## Phase 4: Generating Training Data

Now we'll generate synthetic training examples. Each example shows the model how to respond to a user query.

### Understanding Training Data Format

Each training example should have:

```json
{
  "conversation_id": "unique-id",
  "user_query": "Natural language request",
  "context": "Optional contextual information",
  "tool_calls": [
    {
      "function": "function_name",
      "arguments": {
        "param1": "value1",
        "param2": "value2"
      },
      "reasoning": "Why this function was chosen"
    }
  ],
  "expected_result": "What should happen",
  "complexity": "simple|medium|complex"
}
```

### Script: Generate Training Data

Create `scripts/generate_training_data.py`:

```python
import json
import random
from typing import List, Dict
from openai import OpenAI  # or use any LLM API

class TrainingDataGenerator:
    def __init__(self, functions_path: str, api_key: str = None):
        """
        Initialize with OpenMRS functions and LLM API key.
        You can use GPT-4, Claude, or any capable model.
        """
        with open(functions_path, 'r') as f:
            self.functions = json.load(f)
        
        self.client = OpenAI(api_key=api_key)  # Or use anthropic, etc.
        
    def generate_system_prompt(self) -> str:
        """Create the system prompt for data generation"""
        return """You are an expert at generating realistic OpenMRS administrative queries.

Your task: Generate diverse, realistic user queries that an OpenMRS administrator would ask, along with the correct function calls to handle them.

Guidelines:
1. Generate natural, conversational queries (not robotic)
2. Include typos and informal language occasionally
3. Vary complexity from simple to multi-step workflows
4. Include edge cases (missing info, conflicts, errors)
5. Use realistic medical scenarios and names
6. Include both read and write operations

Output format (JSON):
{
  "user_query": "The natural language query",
  "tool_calls": [
    {
      "function": "function_name",
      "arguments": {"key": "value"},
      "reasoning": "Brief explanation of why"
    }
  ],
  "complexity": "simple|medium|complex",
  "category": "appointments|patients|scheduling|reporting"
}
"""
    
    def generate_examples_for_function(
        self, 
        function: Dict, 
        num_examples: int = 10
    ) -> List[Dict]:
        """
        Generate training examples for a specific function.
        """
        examples = []
        
        # Create prompt with function details
        function_prompt = f"""Generate {num_examples} diverse examples for this OpenMRS function:

Function: {function['name']}
Description: {function['description']}
Method: {function['method']} {function['endpoint']}
Parameters: {json.dumps(function['parameters'], indent=2)}

Include examples with:
- Different phrasings and formality levels
- Missing optional parameters
- Complex multi-step scenarios requiring this function
- Edge cases and error scenarios
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.generate_system_prompt()},
                    {"role": "user", "content": function_prompt}
                ],
                temperature=0.9,  # Higher for diversity
                response_format={"type": "json_object"}
            )
            
            generated = json.loads(response.choices[0].message.content)
            
            # Extract examples (handle different response formats)
            if "examples" in generated:
                examples = generated["examples"]
            elif isinstance(generated, list):
                examples = generated
            else:
                examples = [generated]
            
        except Exception as e:
            print(f"Error generating examples for {function['name']}: {e}")
        
        return examples
    
    def generate_multi_step_scenarios(self, num_scenarios: int = 50) -> List[Dict]:
        """
        Generate complex scenarios requiring multiple function calls.
        """
        scenarios = []
        
        scenario_templates = [
            "Schedule an appointment and send confirmation",
            "Find patient, check their history, update records",
            "Search for available time slots, book appointment, assign provider",
            "Create new patient, schedule initial consultation",
            "Reschedule existing appointment and notify parties",
            "Generate report of appointments for specific date range",
            "Find all patients with specific condition and schedule follow-ups",
            "Check provider availability and schedule multiple appointments"
        ]
        
        for template in random.sample(scenario_templates, min(num_scenarios, len(scenario_templates))):
            prompt = f"""Generate a detailed, realistic scenario based on: "{template}"

Create a JSON object with:
- user_query: Natural language request
- tool_calls: Array of function calls needed (in order)
- reasoning: Step-by-step explanation
- complexity: "complex"
- required_context: What information might be needed

Use realistic medical terminology and OpenMRS workflows."""
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": self.generate_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.9,
                    response_format={"type": "json_object"}
                )
                
                scenario = json.loads(response.choices[0].message.content)
                scenarios.append(scenario)
                
            except Exception as e:
                print(f"Error generating scenario: {e}")
        
        return scenarios
    
    def generate_full_dataset(self, 
                            examples_per_function: int = 5,
                            num_complex_scenarios: int = 100) -> List[Dict]:
        """
        Generate complete training dataset.
        """
        all_examples = []
        
        print(f"Generating examples for {len(self.functions)} functions...")
        
        # Generate examples for each function
        for i, function in enumerate(self.functions[:20]):  # Start with top 20
            print(f"Processing function {i+1}/20: {function['name']}")
            
            examples = self.generate_examples_for_function(
                function, 
                num_examples=examples_per_function
            )
            all_examples.extend(examples)
        
        print(f"\nGenerated {len(all_examples)} function-specific examples")
        
        # Generate complex multi-step scenarios
        print(f"\nGenerating {num_complex_scenarios} complex scenarios...")
        scenarios = self.generate_multi_step_scenarios(num_complex_scenarios)
        all_examples.extend(scenarios)
        
        print(f"\nTotal examples: {len(all_examples)}")
        
        return all_examples
    
    def validate_and_clean(self, examples: List[Dict]) -> List[Dict]:
        """
        Validate and clean generated examples.
        """
        cleaned = []
        
        for example in examples:
            # Check required fields
            if not all(k in example for k in ['user_query', 'tool_calls']):
                continue
            
            # Validate tool calls reference actual functions
            valid = True
            for call in example['tool_calls']:
                func_name = call.get('function', '')
                if not any(f['name'] == func_name for f in self.functions):
                    valid = False
                    break
            
            if valid:
                cleaned.append(example)
        
        print(f"Validated: {len(cleaned)}/{len(examples)} examples")
        return cleaned
    
    def save_dataset(self, examples: List[Dict], output_path: str):
        """Save training dataset"""
        with open(output_path, 'w') as f:
            json.dump(examples, f, indent=2)
        
        # Save statistics
        stats = {
            "total_examples": len(examples),
            "by_complexity": {
                "simple": sum(1 for e in examples if e.get('complexity') == 'simple'),
                "medium": sum(1 for e in examples if e.get('complexity') == 'medium'),
                "complex": sum(1 for e in examples if e.get('complexity') == 'complex')
            }
        }
        
        with open(output_path.replace('.json', '_stats.json'), 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"\nSaved {len(examples)} examples to {output_path}")
        print(f"Statistics: {stats}")


# Usage
if __name__ == "__main__":
    import os
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")  # or ANTHROPIC_API_KEY, etc.
    
    generator = TrainingDataGenerator(
        "data/openmrs_functions.json",
        api_key=api_key
    )
    
    # Generate dataset
    examples = generator.generate_full_dataset(
        examples_per_function=5,
        num_complex_scenarios=100
    )
    
    # Validate and clean
    cleaned_examples = generator.validate_and_clean(examples)
    
    # Save
    generator.save_dataset(cleaned_examples, "data/training_data.json")
```

**Run the script:**

```bash
export OPENAI_API_KEY="your-key-here"  # or ANTHROPIC_API_KEY
python scripts/generate_training_data.py
```

### Alternative: Manual Data Creation

If you don't want to use an LLM for generation, create examples manually:

```python
# data/manual_examples.json
[
  {
    "user_query": "Show me all appointments for Dr. Smith today",
    "tool_calls": [
      {
        "function": "get_practitioner",
        "arguments": {"name": "Dr. Smith"},
        "reasoning": "First find the practitioner ID"
      },
      {
        "function": "get_appointments",
        "arguments": {
          "practitioner_id": "{from_previous}",
          "date": "2024-11-01"
        },
        "reasoning": "Then get their appointments"
      }
    ],
    "complexity": "medium"
  }
]
```

---

## Phase 5: Preparing the Model for Training

Now we'll set up the model with efficient fine-tuning using LoRA (Low-Rank Adaptation).

### Script: Model Setup and Training

Create `scripts/train_model.py`:

```python
import torch
import json
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset
import wandb

class OpenMRSModelTrainer:
    def __init__(self, 
                 model_name: str = "google/gemma-2b-it",
                 output_dir: str = "./models/openmrs-agent"):
        """
        Initialize trainer with model and output directory.
        
        Model options:
        - google/gemma-2b-it (2B params, ~5GB)
        - google/gemma-3-4b-it (4B params, ~8GB) 
        - google/gemma-7b-it (7B params, ~14GB)
        """
        self.model_name = model_name
        self.output_dir = output_dir
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"Using device: {self.device}")
        print(f"Model: {model_name}")
    
    def setup_quantization(self) -> BitsAndBytesConfig:
        """
        Configure 4-bit quantization to reduce memory usage.
        Allows training on GPUs with 16GB VRAM.
        """
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",  # Normal Float 4
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,  # Double quantization for extra savings
        )
    
    def load_model_and_tokenizer(self):
        """Load the base model with quantization"""
        print("Loading model and tokenizer...")
        
        # Quantization config
        bnb_config = self.setup_quantization()
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        
        # Prepare model for k-bit training
        self.model = prepare_model_for_kbit_training(self.model)
        
        print("Model loaded successfully")
    
    def setup_lora(self):
        """
        Configure LoRA (Low-Rank Adaptation).
        This reduces trainable parameters from billions to millions.
        """
        lora_config = LoraConfig(
            r=32,  # Rank - higher = more capacity but more params
            lora_alpha=64,  # Scaling factor
            target_modules=[
                # Target attention and MLP layers
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj"
            ],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        self.model = get_peft_model(self.model, lora_config)
        
        # Print trainable parameters
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.model.parameters())
        
        print(f"Trainable params: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")
        print(f"Total params: {total_params:,}")
    
    def load_and_format_dataset(self, dataset_path: str) -> Dataset:
        """
        Load training data and format for the model.
        """
        print(f"Loading dataset from {dataset_path}...")
        
        with open(dataset_path, 'r') as f:
            data = json.load(f)
        
        # Format each example
        formatted_data = []
        for example in data:
            formatted = self._format_example(example)
            if formatted:
                formatted_data.append(formatted)
        
        print(f"Loaded {len(formatted_data)} training examples")
        
        # Convert to HuggingFace Dataset
        dataset = Dataset.from_list(formatted_data)
        
        return dataset
    
    def _format_example(self, example: Dict) -> Dict:
        """
        Format a single training example into the model's expected format.
        
        We create a chat-style format with:
        - System: Instructions and available functions
        - User: The query
        - Assistant: The tool calls
        """
        # Load function definitions
        with open("data/openmrs_functions.json", 'r') as f:
            functions = json.load(f)
        
        # Create system message with available functions
        system_message = self._create_system_message(functions)
        
        # Format tool calls as text
        tool_calls_text = self._format_tool_calls(example.get('tool_calls', []))
        
        # Build conversation
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": example['user_query']},
            {"role": "assistant", "content": tool_calls_text}
        ]
        
        # Apply chat template and tokenize
        try:
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=False
            )
            
            return {"text": text}
        except Exception as e:
            print(f"Error formatting example: {e}")
            return None
    
    def _create_system_message(self, functions: List[Dict]) -> str:
        """Create system prompt with function definitions"""
        functions_text = "\n".join([
            f"- {f['name']}: {f['description']}"
            for f in functions[:20]  # Include top 20 functions
        ])
        
        return f"""You are an expert OpenMRS administrator assistant. You have access to these functions:

{functions_text}

When a user asks for help, respond with the appropriate function call(s) in JSON format:
{{
  "function": "function_name",
  "arguments": {{"param": "value"}}
}}

For multi-step tasks, provide multiple function calls in order."""
    
    def _format_tool_calls(self, tool_calls: List[Dict]) -> str:
        """Format tool calls as JSON text"""
        if not tool_calls:
            return "No functions needed for this query."
        
        formatted = []
        for call in tool_calls:
            formatted.append({
                "function": call.get('function'),
                "arguments": call.get('arguments', {}),
                "reasoning": call.get('reasoning', '')
            })
        
        return json.dumps(formatted, indent=2)
    
    def train(self, dataset: Dataset, num_epochs: int = 3):
        """
        Train the model with the prepared dataset.
        """
        print("\nStarting training...")
        
        # Initialize Weights & Biases for tracking (optional)
        wandb.init(
            project="openmrs-agent",
            config={
                "model": self.model_name,
                "epochs": num_epochs,
                "dataset_size": len(dataset)
            }
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=4,
            gradient_accumulation_steps=8,  # Effective batch size = 32
            learning_rate=2e-4,
            fp16=False,
            bf16=True,  # Use bfloat16 if supported
            logging_steps=10,
            save_strategy="epoch",
            save_total_limit=2,
            optim="paged_adamw_32bit",  # Efficient optimizer
            warmup_ratio=0.03,
            lr_scheduler_type="cosine",
            group_by_length=True,  # Group similar lengths for efficiency
            report_to="wandb",
            remove_unused_columns=False,
        )
        
        # Data collator for language modeling
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False  # Causal LM, not masked LM
        )
        
        # Tokenize dataset
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=2048,
                padding="max_length"
            )
        
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_dataset,
            data_collator=data_collator,
        )
        
        # Train
        trainer.train()
        
        # Save final model
        trainer.save_model(self.output_dir)
        self.tokenizer.save_pretrained(self.output_dir)
        
        print(f"\nTraining complete! Model saved to {self.output_dir}")
    
    def test_inference(self, test_query: str):
        """Quick test of the trained model"""
        print(f"\nTesting with query: {test_query}")
        
        messages = [
            {"role": "system", "content": "You are an OpenMRS administrator assistant."},
            {"role": "user", "content": test_query}
        ]
        
        inputs = self.tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            add_generation_prompt=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=256,
                temperature=0.1,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"\nModel response:\n{response}")


# Main training script
if __name__ == "__main__":
    # Initialize trainer
    trainer = OpenMRSModelTrainer(
        model_name="google/gemma-2b-it",  # or gemma-3-4b-it
        output_dir="./models/openmrs-agent"
    )
    
    # Load and setup model
    trainer.load_model_and_tokenizer()
    trainer.setup_lora()
    
    # Load training data
    dataset = trainer.load_and_format_dataset("data/training_data.json")
    
    # Train
    trainer.train(dataset, num_epochs=3)
    
    # Test
    trainer.test_inference("Schedule an appointment for John Doe tomorrow at 2pm")
```

**Run training:**

```bash
python scripts/train_model.py
```

**Expected training time:**
- With T4 (Colab): ~2-3 hours for 2000 examples
- With A100: ~30-45 minutes
- With RTX 4090: ~1-2 hours

---

## Phase 6: Building the Agent

Now let's create the actual agent that uses your trained model to execute OpenMRS operations.

### Script: OpenMRS Agent

Create `scripts/agent.py`:

```python
import torch
import json
import requests
from typing import List, Dict, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

class OpenMRSAgent:
    def __init__(self, 
                 model_path: str,
                 openmrs_base_url: str,
                 username: str,
                 password: str):
        """
        Initialize the OpenMRS agent.
        
        Args:
            model_path: Path to your fine-tuned model
            openmrs_base_url: Base URL of OpenMRS (e.g., http://localhost:8080/openmrs)
            username: OpenMRS username
            password: OpenMRS password
        """
        self.openmrs_base = openmrs_base_url
        self.auth = (username, password)
        
        # Load functions catalog
        with open("data/openmrs_functions.json", 'r') as f:
            self.functions = {f['name']: f for f in json.load(f)}
        
        # Load model
        print("Loading model...")
        self.load_model(model_path)
        
        # Conversation history
        self.conversation_history = []
        
        print("Agent initialized successfully")
    
    def load_model(self, model_path: str):
        """Load the fine-tuned model"""
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            trust_remote_code=True
        )
        
        # Load LoRA adapters if they exist
        try:
            self.model = PeftModel.from_pretrained(base_model, model_path)
        except:
            self.model = base_model
        
        self.model.eval()
        print(f"Model loaded on {device}")
    
    def process_query(self, user_query: str, execute: bool = False) -> Dict:
        """
        Process a user query and optionally execute the API calls.
        
        Args:
            user_query: Natural language query from user
            execute: Whether to actually execute API calls (False = dry run)
        
        Returns:
            Dict with model response and execution results
        """
        print(f"\n{'='*60}")
        print(f"Query: {user_query}")
        print(f"{'='*60}")
        
        # Generate response from model
        tool_calls = self._generate_tool_calls(user_query)
        
        if not tool_calls:
            return {
                "status": "no_action",
                "message": "No API calls needed",
                "query": user_query
            }
        
        print(f"\nModel generated {len(tool_calls)} function call(s):")
        for i, call in enumerate(tool_calls, 1):
            print(f"\n{i}. {call['function']}")
            print(f"   Arguments: {json.dumps(call['arguments'], indent=6)}")
            if 'reasoning' in call:
                print(f"   Reasoning: {call['reasoning']}")
        
        # Execute if requested
        results = []
        if execute:
            print("\nExecuting API calls...")
            for call in tool_calls:
                result = self._execute_function(call)
                results.append(result)
                print(f"  ✓ {call['function']}: {result['status']}")
        else:
            print("\n[Dry run - not executing. Set execute=True to run]")
        
        return {
            "status": "success",
            "query": user_query,
            "tool_calls": tool_calls,
            "results": results if execute else None
        }
    
    def _generate_tool_calls(self, user_query: str) -> List[Dict]:
        """Use the model to generate function calls"""
        
        # Build system message with available functions
        system_message = self._build_system_prompt()
        
        # Build conversation
        messages = [
            {"role": "system", "content": system_message},
            *self.conversation_history,  # Include previous turns
            {"role": "user", "content": user_query}
        ]
        
        # Generate
        inputs = self.tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            add_generation_prompt=True
        ).to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=512,
                temperature=0.1,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract JSON from response
        tool_calls = self._extract_json(response_text)
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_query})
        self.conversation_history.append({"role": "assistant", "content": response_text})
        
        # Keep only last 5 turns
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return tool_calls
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with available functions"""
        
        # For efficiency, only include relevant functions
        # In production, use semantic search to retrieve relevant functions
        function_list = "\n".join([
            f"- {name}: {func['description']}"
            for name, func in list(self.functions.items())[:20]
        ])
        
        return f"""You are an expert OpenMRS administrator assistant.

Available functions:
{function_list}

Respond with function call(s) in JSON format:
[
  {{
    "function": "function_name",
    "arguments": {{"param": "value"}},
    "reasoning": "brief explanation"
  }}
]

For multi-step tasks, include all necessary calls in order."""
    
    def _extract_json(self, text: str) -> List[Dict]:
        """Extract JSON function calls from model output"""
        import re
        
        # Try to find JSON array or object
        json_match = re.search(r'\[.*\]|\{.*\}', text, re.DOTALL)
        
        if not json_match:
            return []
        
        try:
            parsed = json.loads(json_match.group())
            
            # Ensure it's a list
            if isinstance(parsed, dict):
                parsed = [parsed]
            
            return parsed
        except json.JSONDecodeError:
            print("Warning: Could not parse JSON from model output")
            return []
    
    def _execute_function(self, function_call: Dict) -> Dict:
        """
        Execute an actual API call to OpenMRS.
        """
        func_name = function_call['function']
        arguments = function_call['arguments']
        
        if func_name not in self.functions:
            return {
                "status": "error",
                "message": f"Unknown function: {func_name}"
            }
        
        func_def = self.functions[func_name]
        
        # Build URL
        url = f"{self.openmrs_base}{func_def['endpoint']}"
        
        # Replace path parameters
        for param_name, param_value in arguments.items():
            url = url.replace(f"{{{param_name}}}", str(param_value))
        
        # Prepare request
        method = func_def['method']
        headers = {"Content-Type": "application/json"}
        
        try:
            if method == "GET":
                response = requests.get(url, auth=self.auth, headers=headers, params=arguments)
            elif method == "POST":
                response = requests.post(url, auth=self.auth, headers=headers, json=arguments)
            elif method == "PUT":
                response = requests.put(url, auth=self.auth, headers=headers, json=arguments)
            elif method == "DELETE":
                response = requests.delete(url, auth=self.auth, headers=headers)
            else:
                return {"status": "error", "message": f"Unsupported method: {method}"}
            
            response.raise_for_status()
            
            return {
                "status": "success",
                "function": func_name,
                "data": response.json() if response.content else None,
                "status_code": response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "function": func_name,
                "message": str(e)
            }
    
    def interactive_mode(self):
        """Run in interactive mode for testing"""
        print("\n" + "="*60)
        print("OpenMRS Agent - Interactive Mode")
        print("="*60)
        print("Commands:")
        print("  'execute' - Toggle auto-execution (currently OFF)")
        print("  'history' - Show conversation history")
        print("  'reset' - Clear conversation history")
        print("  'exit' - Quit")
        print("="*60 + "\n")
        
        auto_execute = False
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'exit':
                    print("Goodbye!")
                    break
                
                elif user_input.lower() == 'execute':
                    auto_execute = not auto_execute
                    print(f"Auto-execution: {'ON' if auto_execute else 'OFF'}")
                    continue
                
                elif user_input.lower() == 'history':
                    print("\nConversation History:")
                    for msg in self.conversation_history:
                        print(f"  {msg['role']}: {msg['content'][:100]}...")
                    continue
                
                elif user_input.lower() == 'reset':
                    self.conversation_history = []
                    print("History cleared")
                    continue
                
                # Process query
                result = self.process_query(user_input, execute=auto_execute)
                
                if result['status'] == 'success' and result.get('results'):
                    print("\nExecution Results:")
                    for res in result['results']:
                        print(f"  {res['function']}: {res['status']}")
                        if res['status'] == 'success' and res.get('data'):
                            print(f"    Data: {json.dumps(res['data'], indent=4)[:200]}...")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


# Usage example
if __name__ == "__main__":
    import os
    
    # Initialize agent
    agent = OpenMRSAgent(
        model_path="./models/openmrs-agent",
        openmrs_base_url=os.getenv("OPENMRS_URL", "http://localhost:8080/openmrs"),
        username=os.getenv("OPENMRS_USER", "admin"),
        password=os.getenv("OPENMRS_PASSWORD", "Admin123")
    )
    
    # Run in interactive mode
    agent.interactive_mode()
```

**Run the agent:**

```bash
export OPENMRS_URL="http://localhost:8080/openmrs"
export OPENMRS_USER="admin"
export OPENMRS_PASSWORD="Admin123"

python scripts/agent.py
```

---

## Phase 7: Evaluation and Testing

Create a comprehensive test suite to evaluate your agent's performance.

### Script: Evaluation

Create `scripts/evaluate.py`:

```python
import json
from typing import List, Dict
from agent import OpenMRSAgent

class AgentEvaluator:
    def __init__(self, agent: OpenMRSAgent, test_cases_path: str):
        self.agent = agent
        
        with open(test_cases_path, 'r') as f:
            self.test_cases = json.load(f)
    
    def run_evaluation(self) -> Dict:
        """Run full evaluation suite"""
        results = {
            "total": len(self.test_cases),
            "passed": 0,
            "failed": 0,
            "details": []
        }
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n[Test {i}/{len(self.test_cases)}] {test_case['description']}")
            
            # Run test
            passed, details = self._run_test(test_case)
            
            if passed:
                results["passed"] += 1
                print("  ✓ PASSED")
            else:
                results["failed"] += 1
                print(f"  ✗ FAILED: {details}")
            
            results["details"].append({
                "test": test_case['description'],
                "passed": passed,
                "details": details
            })
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Evaluation Complete")
        print(f"{'='*60}")
        print(f"Total: {results['total']}")
        print(f"Passed: {results['passed']} ({100*results['passed']/results['total']:.1f}%)")
        print(f"Failed: {results['failed']} ({100*results['failed']/results['total']:.1f}%)")
        
        return results
    
    def _run_test(self, test_case: Dict) -> tuple:
        """Run a single test case"""
        try:
            # Get model response
            response = self.agent.process_query(
                test_case['query'],
                execute=False  # Don't execute during testing
            )
            
            # Check if correct functions were called
            expected_functions = set(test_case['expected_functions'])
            actual_functions = set(call['function'] for call in response['tool_calls'])
            
            if expected_functions != actual_functions:
                return False, f"Expected {expected_functions}, got {actual_functions}"
            
            # Check parameters (basic validation)
            for call in response['tool_calls']:
                if not self._validate_parameters(call, test_case):
                    return False, f"Invalid parameters for {call['function']}"
            
            return True, "All checks passed"
            
        except Exception as e:
            return False, f"Exception: {str(e)}"
    
    def _validate_parameters(self, call: Dict, test_case: Dict) -> bool:
        """Validate that parameters are reasonable"""
        # Basic validation - extend based on your needs
        args = call['arguments']
        
        # Check for required parameters
        func_def = self.agent.functions.get(call['function'])
        if not func_def:
            return False
        
        required_params = [
            p['name'] for p in func_def['parameters'] 
            if p.get('required', False)
        ]
        
        for param in required_params:
            if param not in args:
                return False
        
        return True


# Test cases example
test_cases = [
    {
        "description": "Simple appointment search",
        "query": "Show me all appointments for today",
        "expected_functions": ["get_appointments"],
        "expected_params": {"date": "today"}
    },
    {
        "description": "Multi-step patient scheduling",
        "query": "Schedule John Doe for a checkup tomorrow at 2pm",
        "expected_functions": ["search_patient", "check_availability", "create_appointment"],
        "expected_params": {}
    },
    {
        "description": "Provider schedule query",
        "query": "What's Dr. Smith's schedule this week?",
        "expected_functions": ["search_practitioner", "get_schedule"],
        "expected_params": {}
    }
]

# Save test cases
with open("data/test_cases.json", 'w') as f:
    json.dump(test_cases, f, indent=2)

# Run evaluation
if __name__ == "__main__":
    from agent import OpenMRSAgent
    
    agent = OpenMRSAgent(
        model_path="./models/openmrs-agent",
        openmrs_base_url="http://localhost:8080/openmrs",
        username="admin",
        password="Admin123"
    )
    
    evaluator = AgentEvaluator(agent, "data/test_cases.json")
    results = evaluator.run_evaluation()
    
    # Save results
    with open("outputs/evaluation_results.json", 'w') as f:
        json.dump(results, f, indent=2)
```

---

## Phase 8: Optimization and Deployment

### Adding Tool Retrieval (ToolRAG)

Instead of sending all functions in every prompt, use semantic search to retrieve only relevant ones:

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class ToolRetriever:
    def __init__(self, functions: List[Dict]):
        self.functions = functions
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Pre-compute function embeddings
        function_texts = [
            f"{f['name']}: {f['description']}"
            for f in functions
        ]
        self.embeddings = self.embedder.encode(function_texts)
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve most relevant functions for a query"""
        query_embedding = self.embedder.encode([query])
        
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [self.functions[i] for i in top_indices]
```

Add to your agent:

```python
# In OpenMRSAgent.__init__
self.tool_retriever = ToolRetriever(list(self.functions.values()))

# In _build_system_prompt
relevant_functions = self.tool_retriever.retrieve(user_query, top_k=10)
function_list = "\n".join([
    f"- {f['name']}: {f['description']}"
    for f in relevant_functions
])
```

### Converting to GGUF for Local Use

```bash
# Install llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make

# Convert model
python convert.py ../models/openmrs-agent \
    --outtype f16 \
    --outfile ../models/openmrs-agent.gguf

# Quantize
./quantize ../models/openmrs-agent.gguf \
    ../models/openmrs-agent-q4.gguf Q4_K_M
```

### Safety Validations

Add validation before executing API calls:

```python
class SafetyValidator:
    def __init__(self):
        self.dangerous_operations = ['delete', 'remove', 'drop']
    
    def validate_call(self, function_call: Dict) -> tuple:
        """
        Returns: (is_safe: bool, reason: str)
        """
        func_name = function_call['function'].lower()
        
        # Check for dangerous operations
        if any(op in func_name for op in self.dangerous_operations):
            return False, "Destructive operation requires manual confirmation"
        
        # Validate required parameters exist
        args = function_call['arguments']
        if not args:
            return False, "Missing required parameters"
        
        # Check for suspicious patterns
        if 'id' in args and args['id'] == '*':
            return False, "Wildcard operations not allowed"
        
        return True, "Validation passed"
```

---

## Best Practices & Tips

### 1. Start Small, Iterate

- Begin with 5-10 most common functions
- Test thoroughly before adding more
- Expand based on real usage patterns

### 2. Monitor Performance

```python
import time

def track_performance(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

### 3. Handle Errors Gracefully

```python
try:
    result = self._execute_function(call)
except Exception as e:
    # Log error
    logging.error(f"Function execution failed: {e}")
    
    # Provide helpful message
    return {
        "status": "error",
        "message": "I encountered an error. Please try rephrasing your request.",
        "details": str(e)
    }
```

### 4. Add Human Confirmation for Critical Operations

```python
def requires_confirmation(function_name: str) -> bool:
    critical_ops = ['create_patient', 'update_patient', 'delete_*', 'modify_*']
    return any(pattern in function_name for pattern in critical_ops)

# In process_query
if requires_confirmation(call['function']):
    confirmation = input(f"Confirm {call['function']}? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("Operation cancelled")
        continue
```

### 5. Version Your Models

```bash
models/
  openmrs-agent-v1.0/
  openmrs-agent-v1.1/
  openmrs-agent-v2.0/
```

---

## Troubleshooting

### Issue: Model generates invalid JSON

**Solution:** Add post-processing:

```python
def fix_json(text: str) -> str:
    # Remove markdown code blocks
    text = text.replace('```json', '').replace('```', '')
    
    # Fix common issues
    text = text.replace("'", '"')  # Single to double quotes
    text = re.sub(r',\s*}', '}', text)  # Trailing commas
    
    return text
```

### Issue: Model forgets available functions

**Solution:** Use ToolRAG (shown above) or increase context window

### Issue: Out of memory during training

**Solutions:**
1. Reduce batch size
2. Increase gradient accumulation steps
3. Use smaller model (2B instead of 4B)
4. Enable CPU offloading

```python
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    offload_folder="offload",
    offload_state_dict=True
)
```

---

## Next Steps

Once your basic agent works:

1. **Add More Functions**: Expand to cover all OpenMRS operations
2. **Improve Context**: Add conversation memory and session management
3. **Build UI**: Create a web interface or CLI tool
4. **Add Analytics**: Track which functions are used most
5. **Deploy**: Containerize and deploy to production
6. **Collect Feedback**: Gather real user queries to improve training data

---

## Conclusion

You now have a complete pipeline to build a specialized OpenMRS agent:

1. ✅ Extract API schemas
2. ✅ Generate training data
3. ✅ Fine-tune small models efficiently
4. ✅ Build an agent that executes real API calls
5. ✅ Evaluate and optimize performance

The key insight is that small, specialized models can outperform large general models when trained on high-quality, task-specific data. Your 2-4B parameter agent can become an expert OpenMRS administrator with the right training approach.

Happy building! 🚀