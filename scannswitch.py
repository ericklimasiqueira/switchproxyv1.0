from datetime import datetime
import os
import sys
import subprocess

# ---- Imports com fallback amigável ----
missing = []
try:
    import nmap
except Exception:
    missing.append("python-nmap (pip install python-nmap) + nmap instalado no SO")
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.prompt import Prompt, IntPrompt
    from rich.align import Align
except Exception:
    missing.append("rich (pip install rich)")
try:
    import pyfiglet
except Exception:
    pyfiglet = None
try:
    import openpyxl
except Exception:
    missing.append("openpyxl (pip install openpyxl)")

if missing:
    print("\n[ERRO] Dependências ausentes:\n- " + "\n- ".join(missing))
    sys.exit(1)

console = Console()

# ----------------- Configurações -----------------
FABRICANTES_CAMERAS = ['hikvision', 'intelbras', 'dahua', 'greatek', 'multilaser', 'provision', 'uniview']
PORTAS_INTERESSE = [22, 23, 161, 80, 443]
ARQUIVO_PADRAO = "switches_detectados.xlsx"

# ----------------- UI Helpers -----------------
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    clear()
    title = "SWITCH SCANNER"
    if pyfiglet:
        art = pyfiglet.figlet_format(title, font="Standard")
        console.print(Panel.fit(art, style="cyan", border_style="cyan", padding=(0, 2)))
    else:
        console.print(Panel.fit(Text(title, style="bold cyan"), border_style="cyan"))
    subtitle = Text("Detector de Switches • Exporta para Excel", style="bold yellow")
    console.print(Align.center(subtitle))
    console.print()

def info(msg: str):
    console.print(Panel(msg, border_style="blue", style="white", title="INFO", title_align="left"))

def warn(msg: str):
    console.print(Panel(msg, border_style="yellow", style="white", title="ATENÇÃO", title_align="left"))

def error(msg: str):
    console.print(Panel(msg, border_style="red", style="white", title="ERRO", title_align="left"))

def ok(msg: str):
    console.print(Panel(msg, border_style="green", style="white", title="SUCESSO", title_align="left"))

# ----------------- Entrada segura -----------------
def pedir_rede_base() -> str:
    while True:
        rede = Prompt.ask("[cyan]Digite os 2 primeiros blocos do IP[/cyan] (ex.: 192.168)").strip()
        partes = rede.split(".")
        if len(partes) == 2 and all(p.isdigit() and 0 <= int(p) <= 255 for p in partes):
            return rede
        warn("Formato inválido. Exemplo válido: 192.168")

def pedir_octeto(label: str, minimo=0, maximo=254) -> int:
    while True:
        try:
            val = IntPrompt.ask(f"[cyan]{label}[/cyan]", default=minimo)
            if minimo <= val <= maximo:
                return val
            warn(f"Use um número entre {minimo} e {maximo}.")
        except Exception:
            warn("Entrada inválida. Digite apenas números.")

def pedir_nome_arquivo_padrao(sugestao: str) -> str:
    nome = Prompt.ask("[cyan]Nome do arquivo Excel (enter para padrão)[/cyan]", default=sugestao).strip()
    if not nome.lower().endswith(".xlsx"):
        nome += ".xlsx"
    return nome

# ----------------- Núcleo: Scanner -----------------
def testar_snmp_walk(ip, community='public'):
    """Tenta obter informações SNMP via snmpwalk"""
    try:
        resultado = subprocess.run(
            ['snmpwalk', '-v2c', '-c', community, ip],
            capture_output=True,
            text=True,
            timeout=5
        )
        if resultado.returncode == 0 and resultado.stdout:
            return resultado.stdout.strip().split('\n')[0]
        return None
    except Exception:
        return None

def escanear_faixa(faixa_cidr: str):
    resultados = []
    console.print()
    info(f"Escaneando a rede [bold]{faixa_cidr}[/bold]. Aguarde… ⏳")

    try:
        scanner = nmap.PortScanner()
        scanner.scan(hosts=faixa_cidr, arguments=f"-p {','.join(map(str, PORTAS_INTERESSE))} -sS -T3 -Pn --host-timeout 20s --max-retries 3")
    except Exception as e:
        error(f"Erro ao escanear {faixa_cidr}: {e}")
        return resultados

    hosts = list(scanner.all_hosts())
    if not hosts:
        warn("Nenhum host ativo encontrado nessa faixa.")
        return resultados

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Analisando dispositivos…", total=len(hosts))

        for host in hosts:
            try:
                mac = scanner[host].get("addresses", {}).get("mac", "Desconhecido")
                vendor_map = scanner[host].get("vendor", {})
                vendor = vendor_map.get(mac, "Desconhecido") if mac != "Desconhecido" else "Desconhecido"
                tcp = scanner[host].get("tcp", {})
                portas_abertas = sorted([p for p, data in tcp.items() if data.get("state") == "open"])
                vendor_lower = str(vendor).lower()

                if any(cam in vendor_lower for cam in FABRICANTES_CAMERAS):
                    progress.update(task, advance=1)
                    continue

                modelo_snmp = testar_snmp_walk(host)
                tipo_disp = "🟢 Portas" if any(p in portas_abertas for p in [22, 23, 161]) else "🔵 SNMP"
                resultados.append({
                    "IP": host,
                    "MAC": mac,
                    "Fabricante": vendor,
                    "Portas Abertas": ", ".join(map(str, portas_abertas)) if portas_abertas else "-",
                    "Modelo SNMP": modelo_snmp if modelo_snmp else "Não respondeu",
                    "Tipo": tipo_disp
                })
            finally:
                progress.update(task, advance=1)

    return resultados

# ----------------- Saída: Tabela & Excel -----------------
def mostrar_tabela(dados: list):
    if not dados:
        warn("Nada para mostrar.")
        return
    table = Table(title="Switches Detectados", box=box.SIMPLE_HEAVY, header_style="bold white on dark_cyan")
    table.add_column("IP", style="cyan", justify="left")
    table.add_column("MAC", style="magenta", justify="left")
    table.add_column("Fabricante", style="yellow", justify="left")
    table.add_column("Portas Abertas", style="green", justify="left")
    table.add_column("Modelo SNMP", style="white", justify="left")
    table.add_column("Tipo", style="bold", justify="center")

    for item in dados:
        table.add_row(
            item.get("IP", "-"),
            item.get("MAC", "-"),
            item.get("Fabricante", "-"),
            item.get("Portas Abertas", "-"),
            item.get("Modelo SNMP", "-"),
            item.get("Tipo", "-")
        )

    console.print()
    console.print(table)
    console.print()

def salvar_em_planilha(dados: list, nome_arquivo: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Switches Detectados"
    cabecalho = ["IP", "MAC", "Fabricante", "Portas Abertas", "Modelo SNMP", "Tipo"]
    ws.append(cabecalho)

    for item in dados:
        ws.append([item.get(col, "") for col in cabecalho])

    for coluna in ws.columns:
        comprimentos = [len(str(c.value)) if c.value is not None else 0 for c in coluna]
        largura = max(comprimentos + [len(str(coluna[0].value))]) + 2
        ws.column_dimensions[coluna[0].column_letter].width = min(largura, 60)

    wb.save(nome_arquivo)
    ok(f"Planilha salva como: [bold]{nome_arquivo}[/bold]")

# ----------------- Menu -----------------
def menu() -> int:
    console.print(Panel.fit("Escolha uma opção", border_style="magenta"))
    console.print("[yellow]1[/yellow] — Escanear uma única faixa /24 (ex.: 192.168.15.0/24)")
    console.print("[yellow]2[/yellow] — Escanear várias faixas (range do terceiro octeto)")
    console.print("[yellow]3[/yellow] — Sair")
    return pedir_opcao(1, 3)

def pedir_opcao(minimo: int, maximo: int) -> int:
    while True:
        try:
            op = IntPrompt.ask("[cyan]Opção[/cyan]", default=1)
            if minimo <= op <= maximo:
                return op
            warn(f"Escolha entre {minimo} e {maximo}.")
        except Exception:
            warn("Entrada inválida. Digite apenas números.")

# ----------------- App -----------------
def main():
    banner()
    info("Este programa encontra **switches** na rede (SSH, Telnet ou SNMP acessíveis) e salva tudo em Excel.")

    while True:
        console.print()
        opcao = menu()

        if opcao == 1:
            rede_base = pedir_rede_base()
            octeto = pedir_octeto("Terceiro octeto da faixa (ex.: 15)", 0, 254)
            faixa = f"{rede_base}.{octeto}.0/24"
            resultados = escanear_faixa(faixa)
            mostrar_tabela(resultados)

            ts = datetime.now().strftime("%Y%m%d-%H%M")
            sugestao = f"switches_{rede_base.replace('.', '-')}-{octeto}_{ts}.xlsx"
            nome_arq = pedir_nome_arquivo_padrao(sugestao)
            if resultados:
                salvar_em_planilha(resultados, nome_arq)
            else:
                warn("Nenhum switch foi encontrado nessa faixa. Nada a salvar.")

        elif opcao == 2:
            rede_base = pedir_rede_base()
            inicio = pedir_octeto("Início do range (ex.: 15)", 0, 254)
            fim = pedir_octeto(f"Fim do range (>= {inicio})", inicio, 254)

            todos = []
            for i in range(inicio, fim + 1):
                faixa = f"{rede_base}.{i}.0/24"
                res = escanear_faixa(faixa)
                todos.extend(res)

            mostrar_tabela(todos)
            ts = datetime.now().strftime("%Y%m%d-%H%M")
            sugestao = f"switches_{rede_base.replace('.', '-')}-{inicio}-{fim}_{ts}.xlsx"
            nome_arq = pedir_nome_arquivo_padrao(sugestao)
            if todos:
                salvar_em_planilha(todos, nome_arq)
            else:
                warn("Nenhum switch foi encontrado no range informado. Nada a salvar.")

        elif opcao == 3:
            console.print()
            ok("Saindo. Até mais! 👋")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print()
        warn("Interrompido pelo usuário.")
