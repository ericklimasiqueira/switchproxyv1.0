
# Scanner de Rede e Inventário de Switches via Nmap e SNMP

Este script em Python realiza uma varredura em redes locais para identificar switches e outros dispositivos de rede, coletando informações como IP, MAC, fabricante, portas abertas e descrição via SNMP, e salva os dados em uma planilha Excel.

---

## Funcionalidades

- Escaneia uma faixa de sub-redes especificada para descobrir dispositivos ativos.
- Detecta portas abertas relevantes (22, 23, 80, 443 e 161).
- Exclui dispositivos identificados como câmeras IP de fabricantes conhecidos.
- Consulta dispositivos via SNMP para obter descrições detalhadas.
- Gera um arquivo Excel com os dados coletados, formatado para fácil leitura.

---

## Requisitos

- Python 3.x
- Bibliotecas Python:
  - `nmap`
  - `pysnmp`
  - `openpyxl`

Você pode instalar as bibliotecas necessárias com:

```bash
pip install python-nmap pysnmp openpyxl
```

---

## Uso

1. Configure o intervalo de sub-redes que deseja escanear no trecho:

```python
inicio = 15  # início da faixa (exemplo: 192.168.15.0/24)
fim = 20     # fim da faixa (exemplo: 192.168.20.0/24)
```

2. Execute o script:

```bash
python seu_script.py
```

3. Ao final, será gerado um arquivo `switches_detectados.xlsx` com os resultados da varredura.

---

## Explicação dos principais campos coletados

- **IP:** Endereço IP do dispositivo.
- **MAC:** Endereço MAC do dispositivo.
- **Fabricante:** Fabricante identificado pelo Nmap.
- **Portas Abertas:** Lista de portas TCP detectadas abertas.
- **Modelo SNMP:** Descrição obtida via SNMP (quando disponível).

---

## Observações

- O script utiliza a comunidade SNMP padrão `public`.
- Para melhor funcionamento, execute-o em uma rede onde os dispositivos respondam a consultas SNMP e estejam configurados para responder a varreduras de rede.
- O script ignora dispositivos que aparentam ser câmeras IP para focar na detecção de switches.

---

## Licença

Este projeto está aberto para uso e modificação livre.  
Sinta-se à vontade para adaptar conforme sua necessidade!

---

## Contato

Para dúvidas ou sugestões, entre em contato.

