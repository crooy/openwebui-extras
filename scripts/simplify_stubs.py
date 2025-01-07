#!/usr/bin/env python3
"""Script to simplify Python files into type stubs."""
import os
from typing import List, Optional

import libcst as cst


class StubTransformer(cst.CSTTransformer):
    """Transform Python code into stub definitions."""

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        """Keep class structure but remove method bodies."""
        # Keep decorators, bases, and type parameters
        return updated_node.with_changes(
            body=cst.IndentedBlock(
                body=[
                    # Keep method signatures but replace body with ellipsis
                    node.with_changes(body=cst.SimpleStatementSuite([cst.Expr(cst.Ellipsis())]))
                    if isinstance(node, cst.FunctionDef)
                    else node
                    for node in updated_node.body.body
                    if isinstance(node, (cst.FunctionDef, cst.AnnAssign, cst.SimpleStatementLine))
                ]
            )
        )

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """Keep function signatures but remove bodies."""
        return updated_node.with_changes(body=cst.SimpleStatementSuite([cst.Expr(cst.Ellipsis())]))

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Keep only necessary module-level statements."""
        return updated_node.with_changes(
            body=[
                node
                for node in updated_node.body
                if isinstance(
                    node,
                    (
                        cst.Import,
                        cst.ImportFrom,
                        cst.ClassDef,
                        cst.AnnAssign,
                        cst.Assign,
                        cst.SimpleStatementLine,
                    ),
                )
            ]
        )


def process_file(source_path: str, target_path: str) -> None:
    """Process a single file and convert it to a stub."""
    with open(source_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    # Parse and transform
    module = cst.parse_module(source_code)
    transformed = module.visit(StubTransformer())

    # Write stub file
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(transformed.code)


def main() -> None:
    """Main function."""
    stub_dir = "stubs/open_webui/models"
    for file in os.listdir(stub_dir):
        if file.endswith(".py") and not file.endswith(".pyi"):
            source = os.path.join(stub_dir, file)
            target = os.path.join(stub_dir, f"{file}i")
            print(f"Simplifying {source} -> {target}")
            process_file(source, target)
            os.remove(source)


if __name__ == "__main__":
    main()
