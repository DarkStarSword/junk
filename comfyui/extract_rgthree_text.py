#!/usr/bin/env python3

import json
import os
import sys
from PIL import Image

def extract_metadata_from_png(png_path):
    """Extract the workflow metadata JSON string from a PNG image."""
    with Image.open(png_path) as img:
        if "workflow" in img.info:
            return img.info["workflow"]
    raise ValueError("No ComfyUI workflow metadata found in PNG.")

def find_display_any_nodes(workflow_json):
    """Return a list of node IDs for 'Display Any (rgthree)' nodes."""
    data = json.loads(workflow_json)
    nodes = data.get("nodes", [])

    matches = []
    for n in nodes:
        # 'type' identifies the node type in ComfyUI workflows
        if n.get("type") == "Display Any (rgthree)":
            matches.append(n["id"])

    return matches

def extract_display_any_text(workflow_json, node_id=81):
    """Extract the text field from a Display Any (rgthree) node."""
    data = json.loads(workflow_json)

    nodes = data.get("nodes", {})
    for n in nodes:
        if n['id'] == node_id:
            node = n
            break
    else:
        raise ValueError(f"Node {node_id} not found in workflow.")

    widgets_values = node.get("widgets_values", [])
    if len(widgets_values) != 1:
        raise ValueError(f"Node {node_id} does not contain a value.")

    return widgets_values[0]


def old_main():
    if len(sys.argv) < 2:
        print("Usage: python extract_rgthree_text.py <image.png> [node_id]")
        sys.exit(1)

    png_path = sys.argv[1]
    node_id = int(sys.argv[2]) if len(sys.argv) >= 3 else 81

    # Read metadata
    workflow_json = extract_metadata_from_png(png_path)

    # Extract text
    text = extract_display_any_text(workflow_json, node_id=node_id)

    # Output
    print("Extracted text:\n")
    print(text)
    print("\n---")

    # Write to file
    out_path = os.path.splitext(png_path)[0] + ".txt"

    if os.path.exists(out_path):
        resp = input(f"File '{out_path}' exists. Overwrite? (y/N): ").strip().lower()
        if resp != "y":
            print("Aborted. Not overwriting.")
            return

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Saved text to: {out_path}")

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract rgthree Display Any text from ComfyUI PNG metadata."
    )
    parser.add_argument("files", nargs="+", help="PNG files to process")
    parser.add_argument(
        "--node",
        type=int,
        default=None,
        help="Node ID of the Display Any (rgthree) node. "
             "If omitted, auto-detects a single such node.",
    )

    args = parser.parse_args()

    overwrite_all = False
    skip_all = False

    for png_path in args.files:
        print(f"\n=== Processing {png_path} ===")

        try:
            workflow_json = extract_metadata_from_png(png_path)
        except Exception as e:
            print(f"ERROR: Could not read workflow metadata: {e}")
            continue

        # Determine node ID
        node_id = args.node
        if node_id is None:
            # Auto-detect Display Any (rgthree) nodes
            found = find_display_any_nodes(workflow_json)

            if len(found) == 0:
                print("ERROR: No 'Display Any (rgthree)' nodes in workflow. "
                      "Use --node to specify explicitly.")
                continue
            elif len(found) > 1:
                print("ERROR: Multiple 'Display Any (rgthree)' nodes found: "
                      f"{found}. Use --node to choose one.")
                continue
            else:
                node_id = found[0]
                print(f"Auto-detected Display Any node ID: {node_id}")

        # Extract text
        try:
            text = extract_display_any_text(workflow_json, node_id=node_id)
        except Exception as e:
            print(f"ERROR: Failed to extract node text: {e}")
            continue

        print("\nExtracted text:\n")
        print(text)
        print("\n---")

        out_path = os.path.splitext(png_path)[0] + ".txt"

        # Check for overwrite
        if os.path.exists(out_path):
            if skip_all:
                print(f"Skipped writing (N selected earlier).")
                continue
            if not overwrite_all:
                resp = input(
                    f"File '{out_path}' exists. Overwrite? "
                    "[y]es / [n]o / [A]ll / [N]one: "
                ).strip()

                if resp.lower() == "a":
                    overwrite_all = True
                    print("Will overwrite all existing files.")
                elif resp == "N":
                    skip_all = True
                    print("Will skip overwriting all existing files.")
                    continue
                elif resp.lower() != "y":
                    # default = no
                    print("Skipped writing.")
                    continue
                # If resp == "y", fall through to write normally

        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Saved text to: {out_path}")
        except Exception as e:
            print(f"ERROR: Failed to write output file: {e}")

if __name__ == "__main__":
    main()


