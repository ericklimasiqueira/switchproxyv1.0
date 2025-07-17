import nmap
import openpyxl
from pysnmp.hlapi import *

fabricantes_cameras = ['hikvision', 'intelbras', 'dahua', 'greatek', 'multilaser', 'provision', 'uniview']

def obter_descricao_snmp(ip, community='public'):
    try:
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(community),
            UdpTransportTarget((ip, 161), timeout=1, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))  # sysDescr
        )
        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

        if errorIndication or errorStatus:
            return None

        for name, val in varBinds:
            return str(val)
    except:
        return None

# Escaneia uma sub-rede
def escanear_rede(faixa):
    scanner = nmap.PortScanner()
    print(f"📡 Escaneando {faixa}...")
    scanner.scan(hosts=faixa, arguments='-p 22,23,80,443,161 -sS')
    resultados = []

    for host in scanner.all_hosts():
        ip = host
        mac = scanner[host]['addresses'].get('mac', 'Desconhecido')
        vendor = scanner[host]['vendor'].get(mac, 'Desconhecido') if mac != 'Desconhecido' else 'Desconhecido'
        portas = list(scanner[host].get('tcp', {}).keys())
        vendor_lower = vendor.lower()
        modelo_snmp = obter_descricao_snmp(ip)

        if any(cam in vendor_lower for cam in fabricantes_cameras):
            continue


        if any(p in portas for p in [22, 23, 161]):
            resultados.append({
                'IP': ip,
                'MAC': mac,
                'Fabricante': vendor,
                'Portas Abertas': ', '.join(str(p) for p in portas),
                'Modelo SNMP': modelo_snmp if modelo_snmp else 'Não respondeu'
            })

    return resultados


def salvar_em_planilha(dados, nome_arquivo='switches_detectados.xlsx'):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Switches Detectados"

    cabecalho = ['IP', 'MAC', 'Fabricante', 'Portas Abertas', 'Modelo SNMP']
    ws.append(cabecalho)

    for item in dados:
        ws.append([item[col] for col in cabecalho])

    for col in ws.columns:
        max_len = max(len(str(cell.value)) if cell.value else 0 for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2

    wb.save(nome_arquivo)
    print(f"\n📁 Planilha salva como: {nome_arquivo}")


inicio = 15  # de 192.168.15.0
fim = 20     # até 192.168.20.0


dados_totais = []

for i in range(inicio, fim + 1):
    faixa_ip = f"192.168.{i}.0/24"
    dados = escanear_rede(faixa_ip)
    dados_totais.extend(dados)

salvar_em_planilha(dados_totais)
