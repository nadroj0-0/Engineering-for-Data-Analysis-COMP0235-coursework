# Testing and Validation

Scripts in this directory are for testing and validating the pipeline
without running the full production pipeline.

## Descriptions

- `test_pipeline.sh <num_sequences> [run_name]`
  Runs the pipeline on a small randomly selected subset of sequences.

- `lecturer_example_validation.sh <protein_id>`
  Runs the pipeline on the lecturers provided example input and compares:
  - intermediate artefacts
  - final aggregated CSV outputs

