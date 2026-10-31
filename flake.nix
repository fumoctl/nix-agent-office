{
  description = "100% Declarative Nix Environment for AI Agents: Deep Research (RivalSearchMCP + Scratchpad MCP) & Office Document Generation (.docx, .pptx, .xlsx, .pdf)";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          lib = pkgs.lib;
          py = pkgs.python3Packages;
          extraPkgs = import ./nix/extra-packages.nix { inherit pkgs; };

          # 1. Upstream Official Anthropic Skills (pinned commit & SHA-256)
          anthropicSkillsSrc = pkgs.fetchFromGitHub {
            owner = "anthropics";
            repo = "skills";
            rev = "ca45fc496a3436251f191354091d557da31c15b5";
            hash = "sha256-MkCOANBAqCc1WmNf7S8PsyAphGJAIzEXGyCm8RrCR9M=";
          };

          anthropicSkillsPkg = pkgs.runCommand "anthropic-office-skills" { } ''
            mkdir -p $out/skills
            for skill in docx pptx xlsx pdf doc-coauthoring; do
              cp -r ${anthropicSkillsSrc}/skills/$skill $out/skills/$skill
            done
            chmod -R u+w $out/skills
            substituteInPlace $out/skills/xlsx/scripts/recalc.py \
              --replace-fail '(macro_dir / MACRO_FILENAME).write_text(RECALCULATE_MACRO)' \
              'os.chmod(macro_dir, 0o755); (macro_dir / MACRO_FILENAME).unlink(missing_ok=True); (macro_dir / MACRO_FILENAME).write_text(RECALCULATE_MACRO)'
          '';

          # 2. Upstream RivalSearchMCP Source (pinned commit & SHA-256)
          rivalSearchSrc = pkgs.fetchFromGitHub {
            owner = "damionrashford";
            repo = "RivalSearchMCP";
            rev = "3540fa5a8cf00f6a9f0cef8a3322c1077e8daa1d";
            hash = "sha256-iTDTm40rRjE/7bSpsJGfNyrjo1m4tjRLD74e7j8FDK0=";
          };

          # 3. Declarative Python Derivations: docxtpl, docxcompose, scrapling + rivalsearchmcp
          docxcompose = py.buildPythonPackage {
            pname = "docxcompose";
            version = "2.2.0";
            format = "wheel";
            src = pkgs.fetchurl {
              url = "https://files.pythonhosted.org/packages/e4/70/121090145cb543e48da7421e64036e6484bfbbc40fc619d73599dc22eb2e/docxcompose-2.2.0-py3-none-any.whl";
              sha256 = "fcfec8b0ba7d341bd3280cb92b571ed2f9e868bbd0d6750ea9539e0ab0bb49a1";
            };
            dontCheckRuntimeDeps = true;
            propagatedBuildInputs = with py; [
              babel
              lxml
              python-docx
            ];
            doCheck = false;
          };

          docxtpl = py.buildPythonPackage {
            pname = "docxtpl";
            version = "0.20.2";
            format = "wheel";
            src = pkgs.fetchurl {
              url = "https://files.pythonhosted.org/packages/a4/ad/e07939d8e020e513d3860400413ba1e0e06102c469639b440d921337efef/docxtpl-0.20.2-py3-none-any.whl";
              sha256 = "626d5c570a46a62b2ca73b4d08f1c240fa031a5bc45371e1466a4fe184923d10";
            };
            dontCheckRuntimeDeps = true;
            propagatedBuildInputs = with py; [
              python-docx
              jinja2
              lxml
              docxcompose
            ];
            doCheck = false;
          };

          scrapling = py.buildPythonPackage {
            pname = "scrapling";
            version = "0.5";
            format = "wheel";
            src = pkgs.fetchurl {
              url = "https://files.pythonhosted.org/packages/2e/cb/ef02a29c69329b624ce7627b9d494e1348bb28c7e5b57bea657d1e1319e4/scrapling-0.5-py3-none-any.whl";
              sha256 = "366f0ec9f1e7e998900e6c5e3a4063ea34062326394ced64e5c389b690572726";
            };
            dontCheckRuntimeDeps = true;
            propagatedBuildInputs = with py; [
              lxml
              cssselect
              orjson
              tld
              w3lib
              typing-extensions
              click
              curl-cffi
              playwright
              browserforge
              apify-fingerprint-datapoints
              msgspec
              anyio
              protego
              markdownify
            ];
            # Provide compatibility alias for patchright -> playwright types
            postInstall = ''
              mkdir -p $out/${pkgs.python3.sitePackages}/patchright
              echo "from playwright import *" > $out/${pkgs.python3.sitePackages}/patchright/__init__.py
              echo "from playwright.sync_api import *" > $out/${pkgs.python3.sitePackages}/patchright/sync_api.py
              echo "from playwright.async_api import *" > $out/${pkgs.python3.sitePackages}/patchright/async_api.py
            '';
            doCheck = false;
          };

          rivalsearchmcp = py.buildPythonPackage {
            pname = "rivalsearchmcp";
            version = "1.0.0";
            pyproject = true;
            src = rivalSearchSrc;
            build-system = [ py.hatchling ];
            dontCheckRuntimeDeps = true;
            propagatedBuildInputs = with py; [
              httpx
              lxml
              pillow
              websockets
              requests
              aiohttp
              typing-extensions
              pydantic
              pandas
              urllib3
              python-dotenv
              fastmcp
              markdown
              feedparser
              pypdf
              python-docx
              markdownify
              psutil
              scrapling
              cyclopts
              rich
            ];
            doCheck = false;
          };

          # 4. Complete Python Environment for Office Skills, PDF Processing & Deep Research
          pythonEnv = pkgs.python3.withPackages (ps: [
            # Anthropic Office & PDF Skill Dependencies
            ps.openpyxl
            ps.pandas
            ps.numpy
            ps.defusedxml
            ps.lxml
            ps.pillow
            ps.pypdf
            ps.pdfplumber
            ps.reportlab
            ps.pdf2image
            ps.pytesseract
            ps.pypdfium2
            ps.markitdown
            ps.python-pptx
            ps.python-docx
            ps.beautifulsoup4
            ps.pymupdf
            ps.jinja2
            docxcompose
            docxtpl

            # Deep Research & MCP Dependencies
            scrapling
            rivalsearchmcp
            ps.fastmcp
            ps.mcp
            ps.cyclopts
            ps.rich
            ps.httpx
            ps.aiohttp
            ps.pydantic
            ps.feedparser
            ps.markdown
            ps.markdownify
            ps.psutil
          ] ++ (extraPkgs.pythonPackages ps));

          # 5. Declarative Node.js Modules (docx, pptxgenjs, pdf-lib, pdfjs-dist, react, react-dom, react-icons, sharp)
          rawNodeModules = pkgs.importNpmLock.buildNodeModules {
            npmRoot = ./nix/node;
            nodejs = pkgs.nodejs;
          };

          nodeModules = pkgs.stdenv.mkDerivation {
            pname = "office-agent-node-modules";
            version = "1.0.0";
            src = rawNodeModules;
            dontBuild = true;
            nativeBuildInputs = lib.optionals pkgs.stdenv.isLinux [
              pkgs.autoPatchelfHook
            ];
            buildInputs = lib.optionals pkgs.stdenv.isLinux [
              pkgs.stdenv.cc.cc.lib
              pkgs.zlib
              pkgs.glib
            ];
            installPhase = ''
              mkdir -p $out
              cp -r $src/node_modules $out/node_modules
              chmod -R u+w $out/node_modules
              ln -s ${pkgs.playwright-driver} $out/node_modules/playwright-core
              ln -s ${pkgs.playwright-driver} $out/node_modules/playwright
            '';
          };

          # Metric-compatible fonts for LibreOffice headless rendering & visual QA
          # - Liberation -> Arial, Times New Roman, Courier New
          # - Carlito    -> Calibri
          # - Caladea    -> Cambria
          # - DejaVu     -> Fallback Unicode glyphs
          fontsConf = pkgs.makeFontsConf {
            fontDirectories = [
              pkgs.liberation_ttf
              pkgs.carlito
              pkgs.caladea
              pkgs.dejavu_fonts
            ];
          };

          # Wrapped Node executable with NODE_PATH pre-populated
          officeNode = pkgs.writeShellScriptBin "office-node" ''
            export NODE_PATH="${nodeModules}/node_modules''${NODE_PATH:+:$NODE_PATH}"
            exec ${pkgs.nodejs}/bin/node "$@"
          '';

          # Local Pure-Nix RivalSearchMCP Server (stdio by default, or HTTP when ENVIRONMENT=production)
          rivalSearchMcpBin = pkgs.writeShellScriptBin "rivalsearch-mcp" ''
            exec ${pythonEnv}/bin/python3 ${rivalSearchSrc}/server.py "$@"
          '';

          # RivalSearchMCP CLI Tool (no uv needed)
          rivalSearchCliBin = pkgs.writeShellScriptBin "rival-search" ''
            exec ${pythonEnv}/bin/python3 ${./.agents/skills/rival-search-mcp/scripts/cli.py} "$@"
          '';

          # Research Scratchpad MCP Server (stdio)
          scratchpadMcpBin = pkgs.writeShellScriptBin "scratchpad-mcp" ''
            exec ${pythonEnv}/bin/python3 ${./nix/mcp/scratchpad_server.py} mcp "$@"
          '';

          # Research Scratchpad CLI
          scratchpadCliBin = pkgs.writeShellScriptBin "scratchpad-cli" ''
            exec ${pythonEnv}/bin/python3 ${./nix/mcp/scratchpad_server.py} "$@"
          '';

          # System tools needed by Anthropic Office & PDF skills
          systemTools = [
            pkgs.libreoffice
            pkgs.pandoc
            pkgs.poppler-utils
            pkgs.qpdf
            pkgs.pdftk
            pkgs.tesseract
            pkgs.zip
            pkgs.unzip
            pkgs.jq
            pkgs.ripgrep
            pkgs.fd
            pkgs.curl
            pkgs.git
            pkgs.coreutils
            pkgs.gcc
          ] ++ (with pkgs; [
            # Nixpkgs MCP Servers for Agent Reasoning, Memory, Nixpkgs Discovery & Document Conversion
            mcp-server-sequential-thinking
            mcp-server-memory
            mcp-server-fetch
            markitdown-mcp
            mcp-nixos
          ]) ++ extraPkgs.systemPackages;

          # Polyglot toolchains for building & testing cloned open-source projects in work/repos/
          ossPolyglotTools = (with pkgs; [
            git
            curl
            jq
            ripgrep
            fd
            gnumake
            cmake
            ninja
            pkg-config
            gcc
            clang
            rustc
            cargo
            go
            nodejs
            pnpm
            yarn
            uv
            ruff
            (python3.withPackages (ps: [ ps.pytest ps.pytest-asyncio ps.pip ps.virtualenv ]))
            openssl
            openssl.dev
            zlib
            zlib.dev
            sqlite
            sqlite.dev
          ]) ++ extraPkgs.ossPackages;

          # Linux FHS Sandbox for OSS projects whose test suites download prebuilt binaries/wheels
          ossFhsEnv =
            if pkgs.stdenv.isLinux then
              pkgs.buildFHSEnv {
                name = "oss-fhs";
                targetPkgs = p: ossPolyglotTools ++ (with p; [
                  stdenv.cc.cc.lib
                  glib
                  libxml2
                  libxslt
                  libffi
                  ncurses
                  readline
                  bzip2
                  xz
                  icu
                  curl
                  which
                  file
                  unzip
                  zip
                ]);
                runScript = "bash";
              }
            else
              pkgs.writeShellScriptBin "oss-fhs" ''
                export PATH="${lib.makeBinPath ossPolyglotTools}:$PATH"
                exec ${pkgs.bashInteractive}/bin/bash "$@"
              '';

          # End-to-End Verification Script
          verifyEnvBin = pkgs.writeShellScriptBin "verify-env" ''
            set -euo pipefail
            export PATH="${lib.makeBinPath ([ pythonEnv pkgs.nodejs officeNode rivalSearchMcpBin rivalSearchCliBin scratchpadMcpBin scratchpadCliBin ] ++ systemTools)}:$PATH"
            export NODE_PATH="${nodeModules}/node_modules"
            export FONTCONFIG_FILE="${fontsConf}"
            export SAL_USE_VCLPLUGIN="svp"

            echo "=== [1/5] Verifying Declarative Nix Binaries ==="
            for bin in python3 node soffice pandoc pdftoppm pdftotext pdfimages qpdf pdftk tesseract markitdown rivalsearch-mcp rival-search scratchpad-mcp scratchpad-cli mcp-server-sequential-thinking mcp-server-memory markitdown-mcp; do
              command -v "$bin" >/dev/null
              echo "  [OK] $bin -> $(command -v "$bin")"
            done

            echo "=== [2/5] Verifying Python Libraries ==="
            python3 -c "
            import openpyxl, pandas, numpy, defusedxml, lxml.etree, PIL, pypdf, pdfplumber, reportlab, pdf2image, pytesseract, pypdfium2, markitdown, pptx, docx, docxtpl, docxcompose, bs4, pymupdf, jinja2, fastmcp, mcp, scrapling, rival_search_mcp.server
            print('  [OK] All Python libraries (including docxtpl, docxcompose, bs4, pymupdf) & RivalSearchMCP server imported cleanly.')
            "

            echo "=== [3/5] Verifying Node.js Modules (NODE_PATH) ==="
            node -e "
              const docx = require('docx');
              const pptxgen = require('pptxgenjs');
              const pdflib = require('pdf-lib');
              const React = require('react');
              const ReactDOMServer = require('react-dom/server');
              const fa = require('react-icons/fa');
              const sharp = require('sharp');
              const playwright = require('playwright');
              if (!docx.Document || !pptxgen || !pdflib.PDFDocument || !ReactDOMServer.renderToStaticMarkup || !fa.FaCheck || !sharp || !playwright.chromium) {
                throw new Error('Missing expected exports');
              }
              console.log('  [OK] All Node.js modules (docx, pptxgenjs, pdf-lib, react, react-icons, sharp, playwright) loaded cleanly.');
            "

            echo "=== [4/5] Verifying Research Scratchpad Engine ==="
            TMP_WORK="$(mktemp -d)"
            trap 'rm -rf "$TMP_WORK"' EXIT
            export SCRATCHPAD_DIR="$TMP_WORK/.scratchpad"
            scratchpad-cli init verify-session --topic "Declarative Nix Agent Verification" --goal "End-to-end verification" >/dev/null
            scratchpad-cli add-source verify-session --url "https://nixos.org" --title "NixOS" --confidence high --quality 0.98 >/dev/null
            scratchpad-cli record-table verify-session --name "Metrics" --columns-json '["Metric","Value"]' --rows-json '[["Reproducibility",100]]' >/dev/null
            scratchpad-cli export verify-session --output "$TMP_WORK/dossier.md" >/dev/null
            test -s "$TMP_WORK/dossier.md"
            echo "  [OK] Scratchpad initialized, populated, and exported to Markdown dossier."

            echo "=== [5/5] Verifying End-to-End Office & PDF Generation + Validation (.docx, .pptx, .xlsx, .pdf) ==="
            # 5a. DOCX generation & validation
            node -e "
              const fs = require('fs');
              const { Document, Packer, Paragraph, TextRun, HeadingLevel } = require('docx');
              const doc = new Document({
                sections: [{
                  children: [
                    new Paragraph({ text: 'Nix Agent Research Report', heading: HeadingLevel.HEADING_1 }),
                    new Paragraph({ children: [new TextRun('Generated 100% declaratively with Nix.')] })
                  ]
                }]
              });
              Packer.toBuffer(doc).then(buf => fs.writeFileSync('$TMP_WORK/test.docx', buf));
            "
            python3 ${anthropicSkillsPkg}/skills/docx/scripts/office/validate.py "$TMP_WORK/test.docx"
            echo "  [OK] .docx generated and passed XSD schema validation."

            # 5b. PPTX generation & validation
            node -e "
              const pptxgen = require('pptxgenjs');
              const pres = new pptxgen();
              pres.layout = 'LAYOUT_16x9';
              const slide = pres.addSlide();
              slide.addText('Declarative Deep Research Deck', { x: 0.8, y: 1.5, w: 8.4, h: 1.2, fontSize: 36, bold: true, color: '1E2761' });
              pres.writeFile({ fileName: '$TMP_WORK/test.pptx' });
            "
            python3 ${anthropicSkillsPkg}/skills/pptx/scripts/office/validate.py "$TMP_WORK/test.pptx"
            echo "  [OK] .pptx generated and passed OOXML validation."

            # 5c. XLSX generation & LibreOffice formula recalculation
            python3 -c "
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = 'Model'
            ws['A1'] = 'Item'
            ws['B1'] = 'Amount'
            ws['A2'] = 'Q1'
            ws['B2'] = 120
            ws['A3'] = 'Q2'
            ws['B3'] = 180
            ws['A4'] = 'Total'
            ws['B4'] = '=SUM(B2:B3)'
            wb.save('$TMP_WORK/test.xlsx')
            "
            RECALC_JSON="$(python3 ${anthropicSkillsPkg}/skills/xlsx/scripts/recalc.py "$TMP_WORK/test.xlsx")"
            echo "$RECALC_JSON" | jq -e '.status == "success" and .total_errors == 0 and .total_formulas == 1' >/dev/null
            echo "  [OK] .xlsx generated and recalculated via LibreOffice (0 formula errors)."

            # 5d. PDF generation & Poppler inspection
            python3 -c "
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            c = canvas.Canvas('$TMP_WORK/test.pdf', pagesize=letter)
            c.drawString(72, 720, 'Declarative PDF Deliverable')
            c.save()
            "
            pdftoppm -jpeg -r 100 "$TMP_WORK/test.pdf" "$TMP_WORK/page"
            test -s "$TMP_WORK/page-1.jpg"
            echo "  [OK] .pdf generated and rendered to JPEG via Poppler pdftoppm."

            echo ""
            echo "ALL CHECKS PASSED! Environment is 100% declarative and ready."
          '';
        in
        {
          default = pkgs.buildEnv {
            name = "agent-research-office-suite";
            pathsToLink = [ "/bin" ];
            paths = [
              pythonEnv
              pkgs.nodejs
              officeNode
              rivalSearchMcpBin
              rivalSearchCliBin
              scratchpadMcpBin
              scratchpadCliBin
              verifyEnvBin
            ] ++ systemTools;
          };
          inherit
            pythonEnv
            nodeModules
            anthropicSkillsPkg
            scrapling
            rivalsearchmcp;
          office-node = officeNode;
          rivalsearch-mcp = rivalSearchMcpBin;
          rival-search = rivalSearchCliBin;
          scratchpad-mcp = scratchpadMcpBin;
          scratchpad-cli = scratchpadCliBin;
          verify-env = verifyEnvBin;
          sequential-thinking-mcp = pkgs.mcp-server-sequential-thinking;
          memory-mcp = pkgs.mcp-server-memory;
          markitdown-mcp = pkgs.markitdown-mcp;
          fetch-mcp = pkgs.mcp-server-fetch;
          nixos-mcp = pkgs.mcp-nixos;
          oss-fhs = ossFhsEnv;
        }
      );

      apps = forAllSystems (system:
        let
          pkgs = self.packages.${system};
        in
        {
          default = {
            type = "app";
            program = "${pkgs.verify-env}/bin/verify-env";
          };
          verify-env = {
            type = "app";
            program = "${pkgs.verify-env}/bin/verify-env";
          };
          rivalsearch-mcp = {
            type = "app";
            program = "${pkgs.rivalsearch-mcp}/bin/rivalsearch-mcp";
          };
          rival-search = {
            type = "app";
            program = "${pkgs.rival-search}/bin/rival-search";
          };
          scratchpad-mcp = {
            type = "app";
            program = "${pkgs.scratchpad-mcp}/bin/scratchpad-mcp";
          };
          scratchpad-cli = {
            type = "app";
            program = "${pkgs.scratchpad-cli}/bin/scratchpad-cli";
          };
          office-node = {
            type = "app";
            program = "${pkgs.office-node}/bin/office-node";
          };
          sequential-thinking-mcp = {
            type = "app";
            program = "${pkgs.sequential-thinking-mcp}/bin/mcp-server-sequential-thinking";
          };
          memory-mcp = {
            type = "app";
            program = "${pkgs.memory-mcp}/bin/mcp-server-memory";
          };
          markitdown-mcp = {
            type = "app";
            program = "${pkgs.markitdown-mcp}/bin/markitdown-mcp";
          };
          fetch-mcp = {
            type = "app";
            program = "${pkgs.fetch-mcp}/bin/mcp-server-fetch";
          };
          nixos-mcp = {
            type = "app";
            program = "${pkgs.nixos-mcp}/bin/mcp-nixos";
          };
          oss-fhs = {
            type = "app";
            program = "${pkgs.oss-fhs}/bin/oss-fhs";
          };
        }
      );

      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          selfPkgs = self.packages.${system};
          fontsConf = pkgs.makeFontsConf {
            fontDirectories = [
              pkgs.liberation_ttf
              pkgs.carlito
              pkgs.caladea
              pkgs.dejavu_fonts
            ];
          };
        in
        {
          default = pkgs.mkShell {
            name = "research-office-agent-shell";
            packages = [
              selfPkgs.default
            ];
            shellHook = ''
              export NODE_PATH="${selfPkgs.nodeModules}/node_modules''${NODE_PATH:+:$NODE_PATH}"
              export FONTCONFIG_FILE="${fontsConf}"
              export SAL_USE_VCLPLUGIN="svp"
              export AGENT_WORK_DIR="''${AGENT_WORK_DIR:-$PWD/work}"
              export SCRATCHPAD_DIR="''${SCRATCHPAD_DIR:-$AGENT_WORK_DIR/.scratchpad}"
              mkdir -p "$AGENT_WORK_DIR" "$SCRATCHPAD_DIR"
            '';
          };

          oss-polyglot = pkgs.mkShell {
            name = "oss-polyglot-build-test-shell";
            packages = with pkgs; [
              git
              curl
              jq
              ripgrep
              fd
              gnumake
              cmake
              ninja
              pkg-config
              gcc
              clang
              rustc
              cargo
              go
              nodejs
              pnpm
              yarn
              uv
              ruff
              (python3.withPackages (ps: [ ps.pytest ps.pytest-asyncio ps.pip ps.virtualenv ]))
              openssl
              openssl.dev
              zlib
              zlib.dev
              sqlite
              sqlite.dev
            ] ++ (import ./nix/extra-packages.nix { inherit pkgs; }).ossPackages;
            shellHook = ''
              export AGENT_WORK_DIR="''${AGENT_WORK_DIR:-$PWD/work}"
              mkdir -p "$AGENT_WORK_DIR/repos" "$AGENT_WORK_DIR/.cache"
            '';
          };
        }
      );
    };
}
