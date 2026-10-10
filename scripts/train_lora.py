"""Untested external-GPU recipe. Refuses unreviewed data or small GPUs."""
import argparse
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from project import ROOT, validate_examples

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', action='store_true', help='Actually train after all preflight checks')
    parser.add_argument('--steps', type=int, default=50)
    args = parser.parse_args()
    rows = [json.loads(line) for line in (ROOT / 'data/style-draft.jsonl').read_text(encoding='utf-8').splitlines() if line]
    validate_examples(rows)
    if any(row.get('review_status') != 'approved' for row in rows):
        raise SystemExit('Review every draft row and mark approved before training. No training performed.')
    if shutil.disk_usage(ROOT).free < 150 * 1024**3:
        raise SystemExit('Training/export profile requires at least 150 GiB free disk.')
    from unsloth import FastLanguageModel
    import torch
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise SystemExit('Requires a CUDA GPU supporting bf16; the local GTX 1070 is unsupported.')
    free, total = torch.cuda.mem_get_info()
    if free < 70 * 1024**3:
        raise SystemExit('Use an idle 80GB-class GPU: this profile requires 70 GiB free VRAM.')
    if not args.run:
        print('Preflight passed. No training performed. Re-run with --run only after reviewing data and costs.')
        return
    from datasets import Dataset
    from trl import SFTConfig, SFTTrainer
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name='Qwen/Qwen3-Coder-30B-A3B-Instruct', max_seq_length=2048,
        load_in_4bit=False, dtype=torch.bfloat16)
    model = FastLanguageModel.get_peft_model(
        model, r=16, lora_alpha=32, bias='none',
        target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj', 'gate_up_proj'],
        use_gradient_checkpointing=True, random_state=3407)
    dataset = Dataset.from_list([{'text': tokenizer.apply_chat_template(row['messages'], tokenize=False, add_generation_prompt=False)} for row in rows])
    trainer = SFTTrainer(model=model, tokenizer=tokenizer, train_dataset=dataset,
        args=SFTConfig(output_dir=str(ROOT / 'checkpoints'), dataset_text_field='text',
            per_device_train_batch_size=1, gradient_accumulation_steps=4, max_steps=args.steps,
            learning_rate=2e-4, warmup_steps=5, logging_steps=5, optim='adamw_8bit',
            bf16=True, weight_decay=0.001, lr_scheduler_type='linear', seed=3407, report_to='none'))
    trainer.train()
    model.save_pretrained(str(ROOT / 'checkpoints/foreman-lora'))
    tokenizer.save_pretrained(str(ROOT / 'checkpoints/foreman-lora'))
    model.save_pretrained_merged(str(ROOT / 'merged'), tokenizer, save_method='merged_16bit')
    print('Adapter and merged weights saved. Evaluate before releasing; training alone proves no improvement.')

if __name__ == '__main__':
    main()
