---
name: oss-build-test
description: "Clone, build, run, test, and benchmark external open-source software (OSS) repositories inside work/repos/ using isolated, declarative Nix shells and FHS sandboxes. Use whenever researching an open-source project, verifying how a library/application works in practice, running its test suite, or benchmarking it for a technical report (.docx, .pptx, .xlsx, .pdf)."
---

# Open-Source Software (OSS) Build, Test & Benchmark Skill

When researching an open-source project (e.g., discovered via `rivalsearch` `github_search`), you can go beyond reading static READMEs by cloning, building, testing, and benchmarking the software inside [`work/repos/`](../../../work) using declarative Nix environments.

---

## 1. Golden Rules for OSS Evaluation

1. **Always clone into `work/repos/<project-name>`**:
   - Never clone external repositories outside `work/`. Because `work/*` is gitignored, any repository cloned under `work/repos/<project-name>` has its own isolated `.git` directory and never dirties the host Nix Flake.
2. **Keep `$HOME` clean via `./bin/nix-oss-sandbox`**:
   - Always run builds and tests through `./bin/nix-oss-sandbox`. It automatically redirects `CARGO_HOME`, `GOPATH`, `GOCACHE`, `NPM_CONFIG_CACHE`, `UV_CACHE_DIR`, `PIP_CACHE_DIR`, and `XDG_CACHE_HOME` into `work/.cache/` so language package managers never pollute the user's home directory.
3. **Use `mcp-nixos` to find missing system libraries**:
   - If a project fails to build because it needs a C header or CLI tool (e.g., `libpq`, `protobuf`, `libwebp`, `cmake`), query the **`nixos` MCP server** (`mcp-nixos`) to find the exact Nixpkgs package name and pass it via `--pkgs "<pkg1> <pkg2>"`.

---

## 2. Step-by-Step Workflow

### Step 1: Discover & Clone into `work/repos/`
```bash
mkdir -p work/repos
git clone --depth 1 https://github.com/<owner>/<repo>.git work/repos/<repo>
```

### Step 2: Inspect the Project's Build System
Check what language/build files exist in `work/repos/<repo>`:
- `flake.nix` / `shell.nix` → Native Nix project (`./bin/nix-oss-sandbox` will automatically use its `flake.nix`!)
- `Cargo.toml` → Rust project
- `go.mod` → Go project
- `pyproject.toml` / `requirements.txt` → Python project
- `package.json` / `pnpm-lock.yaml` / `yarn.lock` → Node/TypeScript project
- `CMakeLists.txt` / `meson.build` / `Makefile` → C/C++ project

### Step 3: Build & Run Tests in the Declarative Nix Sandbox

#### Mode A: Default Polyglot Shell (`nix develop .#oss-polyglot`)
Includes `python3`, `uv`, `pytest`, `nodejs`, `pnpm`, `yarn`, `rustc`, `cargo`, `go`, `gcc`, `clang`, `cmake`, `ninja`, `gnumake`, `pkg-config`, and `openssl`:
```bash
./bin/nix-oss-sandbox --dir work/repos/<repo> -- cargo test
./bin/nix-oss-sandbox --dir work/repos/<repo> -- pytest
./bin/nix-oss-sandbox --dir work/repos/<repo> -- go test ./...
```

#### Mode B: Ad-Hoc Pinned Nixpkgs (`--pkgs`)
Pull any additional compilers, databases, or system libraries from our flake's locked `nixpkgs`:
```bash
./bin/nix-oss-sandbox --dir work/repos/<repo> --pkgs "rustc cargo protobuf postgresql" -- cargo test
```

#### Mode C: Linux FHS Compatibility Sandbox (`--fhs`)
When an open-source project's test suite downloads precompiled Linux wheels/binaries (e.g., via `uv`, `pip`, `npm`, `playwright`, or custom build scripts) that expect `/lib64/ld-linux-x86-64.so.2`, `/usr/bin`, or `/lib/libstdc++.so.6`:
```bash
./bin/nix-oss-sandbox --dir work/repos/<repo> --fhs -- uv run pytest
./bin/nix-oss-sandbox --dir work/repos/<repo> --fhs -- npm test
```

### Step 4: Record Empirical Results in the Research Scratchpad
After running tests or benchmarks, log the empirical findings in the `scratchpad` MCP server (or `scratchpad-cli`):
- Log test pass/fail counts, build times, binary sizes, or throughput metrics using `scratchpad_record_table`.
- Verify claims made in the project's README against your actual test run using `scratchpad_verify_claim`.
- Include the empirical tables and charts in your generated `.docx`, `.pptx`, `.xlsx`, and `.pdf` deliverables!
