import os
import glob
from mod import Rule  # Ensure your MØD environment is active


def invert_rules_with_mod(input_dir="inv_rules", output_dir="forward_rules"):
    # 1. Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 2. Find all GML files matching the pattern
    search_pattern = os.path.join(input_dir, "*_inv.gml")
    rule_files = glob.glob(search_pattern)

    if not rule_files:
        print(f"No files ending with '_inv.gml' found in '{input_dir}/'")
        return

    processed_count = 0

    for filepath in rule_files:
        filename = os.path.basename(filepath)
        new_filename = filename.replace("_inv.gml", ".gml")
        output_filepath = os.path.join(output_dir, new_filename)

        try:
            # 1. Read the rule using MØD's parser
            rule = Rule.fromGMLFile(filepath)

            # 2. Invert the rule natively
            forward_rule = rule.makeInverse()

            # 3. Extract the GML string
            gml_string = forward_rule.getGMLString()

            # 4. Save to the new directory
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(gml_string)

            processed_count += 1
            print(f"Inverted: {filename} -> {new_filename}")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"\nSuccess! {processed_count} rules inverted and saved to '{output_dir}/'")


if __name__ == "__main__":
    invert_rules_with_mod()