import subprocess

def run_script(script_name):
    print(f"Running {script_name}...")
    result = subprocess.run(['python', script_name], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Errors in {script_name}:\n{result.stderr}")

if __name__ == "__main__":
    # Run your training and prediction scripts
    run_script('train_predictor.py')
    run_script('train_predictor2.py')
    run_script('auto_trainer.py')
    run_script('auto_trainer2.py')

    # Run report generators
    run_script('generate_accuracy_report.py')
    run_script('generate_accuracy_report2.py')

    print("All scripts completed.")
