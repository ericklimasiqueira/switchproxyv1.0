# Scanner Interativo de Switches com Exportação para Excel

Ferramenta em Python para **descoberta e inventário rápido de switches** em redes locais. O script realiza varreduras em faixas /24 (ou múltiplas faixas) usando **Nmap**, tenta identificar dispositivos via **SNMP** (`snmpwalk`) e **ignora automaticamente câmeras IP** de fabricantes comuns. A interface é **interativa no terminal** (usando [Rich](https://github.com/Textualize/rich)) e os resultados podem ser **exportados para Excel**.

> **Use apenas em redes que você administra.** Varreduras não autorizadas podem violar políticas internas e leis locais.

---

## Sumário
1. [Recursos principais](#recursos-principais)
2. [Como funciona (em alto nível)](#como-funciona-em-alto-nível)
3. [Requisitos](#requisitos)
4. [Instalação (por sistema operacional)](#instalação-por-sistema-operacional)
5. [Como usar (passo a passo)](#como-usar-passo-a-passo)
6. [Saídas geradas (terminal e Excel)](#saídas-geradas-terminal-e-excel)
7. [Personalização](#personalização)
8. [Boas práticas e desempenho](#boas-práticas-e-desempenho)
9. [Solução de problemas](#solução-de-problemas)
10. [Roadmap e contribuições](#roadmap-e-contribuições)
11. [Licença](#licença)

---

## Recursos principais

- **Interface interativa** com menus, banners e feedback visual.
- Varredura de **uma faixa /24** ou de **várias faixas /24** (range do 3º octeto).
- Checagem de **portas de interesse**: `22`, `23`, `80`, `443`, `161`.
- **SNMP opcional** para coletar a primeira resposta do `snmpwalk` (útil para modelo/descrição).
- **Filtro automático de câmeras IP** (Hikvision, Intelbras, Dahua, etc.) para focar em switches.
- **Tabela no terminal** (Rich Table) com colunas úteis.
- **Exportação para Excel** com colunas autoajustadas.
- **Sugestão de nome do arquivo** com timestamp (ex.: `switches_192-168-15_20250131-1432.xlsx`).

---

## Como funciona (em alto nível)

1. **Descoberta com Nmap**  
   O script executa o Nmap com argumentos:
   ```text
   -p 22,23,161,80,443 -sS -T3 -Pn --host-timeout 20s --max-retries 3
   ```
   - `-sS`: SYN scan (geralmente requer privilégios elevados).  
   - `-T3`: equilíbrio entre rapidez e confiabilidade.  
   - `-Pn`: considera hosts como “online” (não faz ping prévio).  
   - `--host-timeout 20s`: evita ficar preso em hosts lentos.  
   - `--max-retries 3`: limita tentativas.

2. **Coleta de metadados**  
   Para cada host ativo, o script coleta IP, MAC, possível fabricante (via mapeamento do Nmap), e portas TCP abertas.

3. **Filtro de câmeras**  
   Se o fabricante (derivado do MAC) corresponder à lista de câmeras conhecidas, o host é ignorado.

4. **Consulta SNMP (opcional)**  
   Executa `snmpwalk -v2c -c public <ip>` com timeout curto, guardando **apenas a primeira linha** da resposta (geralmente uma descrição/modelo).

5. **Classificação do tipo**  
   A coluna **Tipo** mostra:
   - `🟢 Portas` caso alguma entre `22`, `23` ou `161` esteja aberta.  
   - `🔵 SNMP` caso contrário.

6. **Exibição e Exportação**  
   Mostra uma tabela no terminal e permite salvar tudo em **Excel**.

---

## Requisitos

- **Python 3.8+** (recomendado)
- **Dependências Python**:
  - `python-nmap`
  - `rich`
  - `openpyxl`
  - `pyfiglet` *(opcional, apenas para o banner)*
- **Dependências do SO**:
  - **Nmap** instalado e no `PATH`.
  - **snmpwalk** disponível (pacote `net-snmp` ou equivalente).
  - **Permissões elevadas** (Admin/sudo) para `-sS` funcionar corretamente.

Instale as libs Python:

```bash
pip install python-nmap rich openpyxl pyfiglet
```

---

## Instalação (por sistema operacional)

### Windows
1. Instale o **Nmap** (inclui **Npcap**): https://nmap.org/download.html  
   - Durante a instalação, selecione a opção de instalar o Npcap.
2. Instale o **Net-SNMP** para ter `snmpwalk` (ex.: “Net-SNMP for Windows”).  
3. Use **Prompt de Comando/PowerShell como Administrador** para executar o script.

### Linux (Debian/Ubuntu)
```bash
sudo apt update
sudo apt install nmap snmp snmpd snmp-mibs-downloader -y   # fornece 'snmpwalk'
# (snmpd é o serviço. Para apenas cliente SNMP, 'snmp' basta.)
```
> Em algumas distros, o pacote do cliente SNMP pode se chamar `snmp` ou `net-snmp`.

### Linux (RHEL/CentOS/Fedora)
```bash
sudo dnf install nmap net-snmp net-snmp-utils -y
```

### macOS
- Instale Homebrew (se não tiver).
```bash
brew install nmap net-snmp
```

---

## Como usar (passo a passo)

1. **Execute o script** (de preferência com privilégios elevados):
   ```bash
   python scannswitch.py
   ```

2. **Menu principal**  
   - `1` — Escanear **uma única faixa /24** (ex.: `192.168.15.0/24`).  
   - `2` — Escanear **várias faixas /24** (range do 3º octeto).  
   - `3` — Sair.

3. **Entradas solicitadas**  
   - **Dois primeiros blocos do IP**: exemplo `192.168`.  
   - **Terceiro octeto** (modo 1) ou **início/fim** (modo 2).

4. **Acompanhe o progresso** no terminal (barra e tempo estimado).

5. **Revise a tabela** exibida ao final da(s) varredura(s).

6. **Salve em Excel** quando for solicitado o nome do arquivo.  
   - O script sugere um nome com **timestamp**.  
   - Você pode aceitar (Enter) ou digitar outro (`.xlsx` será adicionado se faltar).

---

## Saídas geradas (terminal e Excel)

### No terminal
Tabela “**Switches Detectados**” com colunas:
- **IP**
- **MAC**
- **Fabricante**
- **Portas Abertas**
- **Modelo SNMP** *(primeira linha do `snmpwalk`, se houver)*
- **Tipo** (`🟢 Portas` ou `🔵 SNMP`)

### No Excel
- Planilha: **“Switches Detectados”**
- Colunas idênticas às exibidas no terminal.
- Larguras **autoajustadas** para facilitar a leitura.
- Nome sugerido do arquivo: `switches_<base>-<faixa>_<YYYYMMDD-HHMM>.xlsx`  
  Ex.: `switches_192-168-15-20_20250131-1432.xlsx`

---

## Personalização

Abra `scannswitch.py` e ajuste conforme necessário:

1. **Lista de câmeras ignoradas**  
   ```python
   FABRICANTES_CAMERAS = ['hikvision', 'intelbras', 'dahua', 'greatek', 'multilaser', 'provision', 'uniview']
   ```
   > Adicione/remova marcas conforme sua realidade.

2. **Portas escaneadas**  
   ```python
   PORTAS_INTERESSE = [22, 23, 161, 80, 443]
   ```
   > Inclua outras portas (ex.: 8200, 8080) para seu ambiente.

3. **Comunidade SNMP (padrão `public`)**  
   O script chama `testar_snmp_walk(host)` com a comunidade padrão.  
   Para alterar globalmente, mude o **default** da função:
   ```python
   def testar_snmp_walk(ip, community='minhaCommunity'):
       ...
   ```

4. **Parâmetros do Nmap**  
   Dentro de `escanear_faixa`, você pode ajustar a linha:
   ```python
   scanner.scan(hosts=faixa_cidr, arguments="-p 22,23,161,80,443 -sS -T3 -Pn --host-timeout 20s --max-retries 3")
   ```
   - `-T4` acelera, mas pode aumentar falsos negativos em redes instáveis.
   - Remover `-Pn` fará um ping prévio (pode ser bloqueado por firewall).
   - `--host-timeout` e `--max-retries` influenciam duração/precisão.

5. **Nome padrão de arquivo**  
   Existe a constante `ARQUIVO_PADRAO = "switches_detectados.xlsx"`.  
   O fluxo atual usa **nomes sugeridos com timestamp**; ajuste se preferir sempre o padrão.

---

## Boas práticas e desempenho

- **Execute como Admin/sudo** para que o `-sS` (SYN scan) funcione corretamente.
- Em redes muito grandes, prefira varrer **por blocos** (ex.: 10–20, depois 21–30) para manter o controle.
- Se houver **IDS/IPS** sensível, alinhe com o time de segurança antes de varrer.
- Ajuste `-T` e `--host-timeout` conforme a **latência** da rede.
- Caso muitos dispositivos não respondam SNMP, avalie remover a chamada ao `snmpwalk` para ganhar tempo, ou aumentar o timeout.

---

## Solução de problemas

- **“Dependências ausentes” no início**  
  O script lista exatamente o que falta (ex.: `python-nmap`, `rich`, `openpyxl`, `nmap` no SO, `snmpwalk`). Instale e rode novamente.

- **“nmap: command not found” ou “Nmap não encontrado”**  
  Instale o Nmap e **reinicie o terminal** para atualizar o PATH.

- **SYN scan falhando / sem resultados**  
  Execute como **Administrador** (Windows) ou com `sudo` (Linux/macOS). Sem privilégios, o `-sS` pode falhar. Alternativamente, troque para `-sT` (mais lento, porém sem privilégios elevados).

- **`snmpwalk` não retorna**  
  - Verifique se a comunidade (`public` por padrão) está correta.  
  - Confirme se o dispositivo **permite SNMP v2c** a partir da sua sub-rede.  
  - Firewalls podem bloquear UDP/161.

- **Fabricante/MAC “Desconhecido”**  
  O Nmap nem sempre mapeia o fabricante a partir do MAC. Isso é normal em alguns cenários (VLANs, roteamento L3, ARP filtrado).

- **Nenhum host encontrado**  
  - Remova `-Pn` para permitir ping (se a rede responder ICMP).  
  - Verifique se o range está correto e se há conectividade.

---

## Roadmap e contribuições

- [ ] Permitir **definir a comunidade SNMP** via argumento/flag na execução.
- [ ] Suporte a **exportação CSV** adicional ao Excel.
- [ ] Opção para **salvar logs detalhados** por host/porta.
- [ ] Modo **“apenas switches”** com heurísticas extras (LLDP/CDP quando disponível).

Contribuições são bem-vindas! Faça um fork, crie uma branch com sua melhoria e abra um **Pull Request**. Sugestões de melhoria via **Issues** também ajudam muito.

---

## Licença

Uso e modificação livres. Adapte conforme suas necessidades.

---

### Aviso
Este projeto é fornecido “no estado em que se encontra”, **sem garantias**. O autor não se responsabiliza por usos indevidos ou danos causados pelo uso da ferramenta.