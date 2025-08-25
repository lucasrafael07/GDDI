# -*- coding: utf-8 -*-
"""
Dicionário de dados do layout IQVIA para documentação e referência.
Contém descrições, tipos, tamanhos e formatos de todos os campos do layout IQVIA.
"""
from typing import Dict, Any, Optional, List

IQVIA_DATA_DICTIONARY = {
    "data": {
        "desc": "Data de referência do arquivo",
        "tipo": "string",
        "formato": "YYYY-MM-DD",
        "tamanho": 10,
        "obrigatorio": True,
        "exemplo": "2023-05-10"
    },
    "estabelecimentos": {
        "desc": "Lista de estabelecimentos",
        "tipo": "array",
        "obrigatorio": True,
        "campos": {
            "cod": {
                "desc": "Código do estabelecimento no sistema de origem",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            },
            "doc": {
                "desc": "CNPJ do estabelecimento",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "Somente números, sem máscara"
            },
            "nome": {
                "desc": "Nome do estabelecimento",
                "tipo": "string",
                "tamanho": 40,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            },
            "nomeOfc": {
                "desc": "Nome oficial/razão social do estabelecimento",
                "tipo": "string",
                "tamanho": 40,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            },
            "tipo": {
                "desc": "Tipo de estabelecimento",
                "tipo": "string",
                "tamanho": 3,
                "obrigatorio": True,
                "valores": ["CD", "F"],
                "formato": "CD = Centro de Distribuição, F = Filial"
            },
            "tipoCaptacaoPrescricao": {
                "desc": "Tipo de captação de prescrição",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [0, 1, 2, 3],
                "formato": "0 = Não captura, 1 = Captura física, 2 = Captura digital, 3 = Ambos"
            },
            "ender": {
                "desc": "Endereço do estabelecimento",
                "tipo": "object",
                "obrigatorio": True,
                "campos": {
                    "descr": {
                        "desc": "Descrição do endereço",
                        "tipo": "string",
                        "tamanho": 70,
                        "obrigatorio": True,
                        "formato": "Alfa-numérico"
                    },
                    "compl": {
                        "desc": "Complemento do endereço",
                        "tipo": "string",
                        "tamanho": 20,
                        "obrigatorio": False,
                        "formato": "Alfa-numérico"
                    },
                    "cep": {
                        "desc": "CEP",
                        "tipo": "string",
                        "tamanho": 8,
                        "obrigatorio": True,
                        "formato": "Somente números, sem máscara"
                    },
                    "cidade": {
                        "desc": "Cidade",
                        "tipo": "string",
                        "tamanho": 40,
                        "obrigatorio": True,
                        "formato": "Alfa-numérico"
                    },
                    "uf": {
                        "desc": "Estado (UF)",
                        "tipo": "string",
                        "tamanho": 2,
                        "obrigatorio": True,
                        "formato": "Sigla do estado (2 letras)"
                    },
                    "tel": {
                        "desc": "Telefone",
                        "tipo": "string",
                        "tamanho": 20,
                        "obrigatorio": True,
                        "formato": "Somente números, sem máscara"
                    }
                }
            },
            "codIqvia": {
                "desc": "Código do estabelecimento na IQVIA",
                "tipo": "string",
                "tamanho": 10,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            }
        }
    },
    "clientes": {
        "desc": "Lista de clientes",
        "tipo": "array",
        "obrigatorio": True,
        "campos": {
            "tipo": {
                "desc": "Tipo de cliente",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [1, 2],
                "formato": "1 = Pessoa Física, 2 = Pessoa Jurídica"
            },
            "cod": {
                "desc": "Código do cliente no sistema de origem",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            },
            "profSaude": {
                "desc": "Indica se o cliente é profissional de saúde",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [0, 1],
                "formato": "0 = Não é profissional de saúde, 1 = É profissional de saúde"
            },
            "doc": {
                "desc": "Documento do cliente (CPF ou CNPJ)",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": False,
                "formato": "Somente números, sem máscara"
            },
            "nome": {
                "desc": "Nome do cliente",
                "tipo": "string",
                "tamanho": 40,
                "obrigatorio": False,
                "formato": "Alfa-numérico"
            },
            "nomeOfc": {
                "desc": "Nome oficial/razão social do cliente",
                "tipo": "string",
                "tamanho": 40,
                "obrigatorio": False,
                "formato": "Alfa-numérico"
            },
            "ender": {
                "desc": "Endereço do cliente",
                "tipo": "object",
                "obrigatorio": True,
                "campos": {
                    "descr": {
                        "desc": "Descrição do endereço",
                        "tipo": "string",
                        "tamanho": 70,
                        "obrigatorio": False,
                        "formato": "Alfa-numérico"
                    },
                    "compl": {
                        "desc": "Complemento do endereço",
                        "tipo": "string",
                        "tamanho": 20,
                        "obrigatorio": False,
                        "formato": "Alfa-numérico"
                    },
                    "cep": {
                        "desc": "CEP",
                        "tipo": "string",
                        "tamanho": 8,
                        "obrigatorio": True,
                        "formato": "Somente números, sem máscara"
                    },
                    "cidade": {
                        "desc": "Cidade",
                        "tipo": "string",
                        "tamanho": 40,
                        "obrigatorio": True,
                        "formato": "Alfa-numérico"
                    },
                    "uf": {
                        "desc": "Estado (UF)",
                        "tipo": "string",
                        "tamanho": 2,
                        "obrigatorio": True,
                        "formato": "Sigla do estado (2 letras)"
                    },
                    "tel": {
                        "desc": "Telefone",
                        "tipo": "string",
                        "tamanho": 20,
                        "obrigatorio": False,
                        "formato": "Somente números, sem máscara"
                    }
                }
            }
        }
    },
    "profissionaisSaude": {
        "desc": "Lista de profissionais de saúde",
        "tipo": "array",
        "obrigatorio": True,
        "campos": {
            "cod": {
                "desc": "Código do profissional no sistema de origem",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            },
            "doc": {
                "desc": "Documento do profissional (CRM, CRO, etc.)",
                "tipo": "string",
                "tamanho": 20,
                "obrigatorio": True,
                "formato": "Formato: sigla + números + UF (ex: CRM000091475SP)"
            },
            "nome": {
                "desc": "Nome do profissional",
                "tipo": "string",
                "tamanho": 40,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            },
            "local": {
                "desc": "Local de trabalho do profissional",
                "tipo": "object",
                "obrigatorio": True,
                "campos": {
                    "doc": {
                        "desc": "CNPJ do local",
                        "tipo": "string",
                        "tamanho": 14,
                        "obrigatorio": False,
                        "formato": "Somente números, sem máscara"
                    },
                    "nome": {
                        "desc": "Nome do local",
                        "tipo": "string",
                        "tamanho": 40,
                        "obrigatorio": False,
                        "formato": "Alfa-numérico"
                    },
                    "nomeOfc": {
                        "desc": "Nome oficial/razão social do local",
                        "tipo": "string",
                        "tamanho": 40,
                        "obrigatorio": False,
                        "formato": "Alfa-numérico"
                    },
                    "ender": {
                        "desc": "Endereço do local",
                        "tipo": "object",
                        "obrigatorio": True,
                        "campos": {
                            "descr": {
                                "desc": "Descrição do endereço",
                                "tipo": "string",
                                "tamanho": 70,
                                "obrigatorio": True,
                                "formato": "Alfa-numérico"
                            },
                            "compl": {
                                "desc": "Complemento do endereço",
                                "tipo": "string",
                                "tamanho": 20,
                                "obrigatorio": False,
                                "formato": "Alfa-numérico"
                            },
                            "cep": {
                                "desc": "CEP",
                                "tipo": "string",
                                "tamanho": 8,
                                "obrigatorio": True,
                                "formato": "Somente números, sem máscara"
                            },
                            "cidade": {
                                "desc": "Cidade",
                                "tipo": "string",
                                "tamanho": 40,
                                "obrigatorio": True,
                                "formato": "Alfa-numérico"
                            },
                            "uf": {
                                "desc": "Estado (UF)",
                                "tipo": "string",
                                "tamanho": 2,
                                "obrigatorio": True,
                                "formato": "Sigla do estado (2 letras)"
                            },
                            "tel": {
                                "desc": "Telefone",
                                "tipo": "string",
                                "tamanho": 20,
                                "obrigatorio": False,
                                "formato": "Somente números, sem máscara"
                            }
                        }
                    }
                }
            },
            "celular": {
                "desc": "Telefone celular do profissional",
                "tipo": "string",
                "tamanho": 11,
                "obrigatorio": False,
                "formato": "Somente números, sem máscara"
            },
            "email": {
                "desc": "Email do profissional",
                "tipo": "string",
                "tamanho": 80,
                "obrigatorio": False,
                "formato": "Email válido"
            },
            "especialidade": {
                "desc": "Especialidade do profissional",
                "tipo": "string",
                "tamanho": 40,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            },
            "faixaEtaria": {
                "desc": "Faixa etária do profissional",
                "tipo": "integer",
                "obrigatorio": False,
                "valores": [1, 2, 3, 4, 5, 6, 7],
                "formato": "1 = 0-11 anos, 2 = 12-17 anos, 3 = 18-25 anos, 4 = 26-35 anos, 5 = 36-50 anos, 6 = 51-65 anos, 7 = 66+ anos"
            },
            "genero": {
                "desc": "Gênero do profissional",
                "tipo": "string",
                "tamanho": 1,
                "obrigatorio": False,
                "valores": ["M", "F", "N"],
                "formato": "M = Masculino, F = Feminino, N = Não declarado/Outro"
            }
        }
    },
    "pacientes": {
        "desc": "Lista de pacientes",
        "tipo": "array",
        "obrigatorio": True,
        "campos": {
            "cod": {
                "desc": "Código do paciente no sistema de origem",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            },
            "faixaEtaria": {
                "desc": "Faixa etária do paciente",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [1, 2, 3, 4, 5, 6, 7],
                "formato": "1 = 0-11 anos, 2 = 12-17 anos, 3 = 18-25 anos, 4 = 26-35 anos, 5 = 36-50 anos, 6 = 51-65 anos, 7 = 66+ anos"
            },
            "genero": {
                "desc": "Gênero do paciente",
                "tipo": "string",
                "tamanho": 1,
                "obrigatorio": True,
                "valores": ["M", "F", "N"],
                "formato": "M = Masculino, F = Feminino, N = Não declarado/Outro"
            },
            "faixaPeso": {
                "desc": "Faixa de peso do paciente",
                "tipo": "integer",
                "obrigatorio": False,
                "valores": [1, 2, 3, 4, 5, 6, 7],
                "formato": "1 = 0-20kg, 2 = 21-40kg, 3 = 41-60kg, 4 = 61-80kg, 5 = 81-100kg, 6 = 101-120kg, 7 = 121+ kg"
            },
            "altura": {
                "desc": "Altura do paciente em metros",
                "tipo": "number",
                "obrigatorio": False,
                "formato": "Número decimal (ex: 1.75)"
            }
        }
    },
    "produtos": {
        "desc": "Lista de produtos",
        "tipo": "array",
        "obrigatorio": True,
        "campos": {
            "cod": {
                "desc": "Código do produto no sistema de origem",
                "tipo": "string",
                "tamanho": 13,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            },
            "eanSellIn": {
                "desc": "Código de barras na compra",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "EAN/GTIN (somente números)"
            },
            "eanSellOut": {
                "desc": "Código de barras na venda",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "EAN/GTIN (somente números)"
            },
            "qrcode": {
                "desc": "QR Code do produto",
                "tipo": "string",
                "tamanho": 500,
                "obrigatorio": False,
                "formato": "URL ou texto do QR Code"
            },
            "ncm": {
                "desc": "Código NCM do produto",
                "tipo": "string",
                "tamanho": 8,
                "obrigatorio": True,
                "formato": "Somente números"
            },
            "apresent": {
                "desc": "Apresentação do produto",
                "tipo": "string",
                "tamanho": 70,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            },
            "fabr": {
                "desc": "Fabricante do produto",
                "tipo": "string",
                "tamanho": 40,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            },
            "molecula": {
                "desc": "Molécula do produto",
                "tipo": "string",
                "tamanho": 100,
                "obrigatorio": False,
                "formato": "Alfa-numérico"
            },
            "precoFabrica": {
                "desc": "Preço de fábrica do produto",
                "tipo": "number",
                "obrigatorio": True,
                "formato": "Número decimal com 2 casas decimais"
            },
            "dispViaFarmaciaPopular": {
                "desc": "Dispensação via Farmácia Popular",
                "tipo": "string",
                "obrigatorio": True,
                "valores": ["0", "1"],
                "formato": "0 = Não, 1 = Sim"
            },
            "dispViaPbm": {
                "desc": "Dispensação via PBM",
                "tipo": "string",
                "obrigatorio": True,
                "valores": ["0", "1"],
                "formato": "0 = Não, 1 = Sim"
            },
            "marcaPropria": {
                "desc": "Produto de marca própria",
                "tipo": "string",
                "obrigatorio": True,
                "valores": ["0", "1"],
                "formato": "0 = Não, 1 = Sim"
            }
        }
    },
    "vendas": {
        "desc": "Lista de vendas",
        "tipo": "array",
        "obrigatorio": True,
        "campos": {
            "codEstab": {
                "desc": "Código do estabelecimento",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "Alfa-numérico, deve existir em estabelecimentos.cod"
            },
            "codCliente": {
                "desc": "Código do cliente",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "Alfa-numérico, deve existir em clientes.cod"
            },
            "comPrescricao": {
                "desc": "Venda com prescrição",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [0, 1],
                "formato": "0 = Sem prescrição, 1 = Com prescrição"
            },
            "idPrescricao": {
                "desc": "ID da prescrição",
                "tipo": "integer",
                "obrigatorio": False,
                "formato": "Número inteiro, referência para prescricoes.id"
            },
            "paraUsoProfSaude": {
                "desc": "Produto para uso de profissional de saúde",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [0, 1],
                "formato": "0 = Não, 1 = Sim"
            },
            "codProfSaude": {
                "desc": "Código do profissional de saúde",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "Alfa-numérico, deve existir em profissionaisSaude.cod"
            },
            "codProd": {
                "desc": "Código do produto",
                "tipo": "string",
                "tamanho": 13,
                "obrigatorio": True,
                "formato": "Alfa-numérico, deve existir em produtos.cod"
            },
            "dt": {
                "desc": "Data da venda",
                "tipo": "string",
                "tamanho": 10,
                "obrigatorio": True,
                "formato": "YYYY-MM-DD"
            },
            "qt": {
                "desc": "Quantidade vendida",
                "tipo": "integer",
                "obrigatorio": True,
                "formato": "Número inteiro positivo"
            },
            "ecommerce": {
                "desc": "Venda por e-commerce",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [0, 1],
                "formato": "0 = Não, 1 = Sim"
            },
            "meio": {
                "desc": "Meio de venda",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [1, 2, 3, 4, 5, 6, 7, 8, 9],
                "formato": "1 = App próprio, 2 = Site próprio, 3 = Marketplace, 4 = Televendas, 5 = Balcão, 6 = Delivery, 7 = WhatsApp, 8 = Memed, 9 = Outros"
            },
            "docTipo": {
                "desc": "Tipo de documento fiscal",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [0, 1, 2, 3],
                "formato": "0 = Não informado, 1 = Cupom Fiscal, 2 = NF-e, 3 = NFC-e"
            },
            "docFiscalSerie": {
                "desc": "Série do documento fiscal",
                "tipo": "string",
                "tamanho": 3,
                "obrigatorio": True,
                "formato": "Alfa-numérico"
            },
            "docFiscalNum": {
                "desc": "Número do documento fiscal",
                "tipo": "integer",
                "obrigatorio": True,
                "formato": "Número inteiro positivo"
            },
            "danfe": {
                "desc": "Chave da NF-e/NFC-e",
                "tipo": "string",
                "tamanho": 44,
                "obrigatorio": False,
                "formato": "Somente números, 44 dígitos"
            },
            "vendaJudic": {
                "desc": "Venda judicial",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [0, 1],
                "formato": "0 = Não, 1 = Sim"
            },
            "tipoPagto": {
                "desc": "Tipo de pagamento",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [0, 1, 2, 3, 4, 5, 6, 7],
                "formato": "0 = Não informado, 1 = Dinheiro, 2 = Cartão de crédito, 3 = Cartão de débito, 4 = Cheque, 5 = Boleto, 6 = PayPal, 7 = Outros"
            },
            "preco": {
                "desc": "Informações de preço",
                "tipo": "object",
                "obrigatorio": True,
                "campos": {
                    "valor": {
                        "desc": "Valores do produto",
                        "tipo": "object",
                        "obrigatorio": True,
                        "campos": {
                            "liquido": {
                                "desc": "Valor líquido",
                                "tipo": "number",
                                "obrigatorio": True,
                                "formato": "Número decimal com 2 casas decimais"
                            },
                            "bruto": {
                                "desc": "Valor bruto",
                                "tipo": "number",
                                "obrigatorio": True,
                                "formato": "Número decimal com 2 casas decimais"
                            }
                        }
                    },
                    "desconto": {
                        "desc": "Informações de desconto",
                        "tipo": "object",
                        "obrigatorio": False,
                        "campos": {
                            "paraConsumidorFinal": {
                                "desc": "Tipo de desconto para consumidor final",
                                "tipo": "integer",
                                "obrigatorio": True,
                                "valores": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                                "formato": "1 = Desconto comercial, 2 = Promoção, 3 = Black Friday, 4 = Liquidação, 5 = Desconto funcionário, 6 = Desconto fidelidade, 7 = Desconto convênio, 8 = Desconto corporativo, 9 = Desconto governo, 10 = Desconto terceira idade, 11 = Desconto estudante, 12 = Brinde"
                            },
                            "docLabPbm": {
                                "desc": "CNPJ do laboratório PBM",
                                "tipo": "string",
                                "tamanho": 14,
                                "obrigatorio": False,
                                "formato": "Somente números, sem máscara"
                            },
                            "perc": {
                                "desc": "Percentual de desconto",
                                "tipo": "number",
                                "obrigatorio": True,
                                "formato": "Número decimal com 2 casas decimais"
                            },
                            "valor": {
                                "desc": "Valor do desconto",
                                "tipo": "number",
                                "obrigatorio": True,
                                "formato": "Número decimal com 2 casas decimais"
                            }
                        }
                    },
                    "icms": {
                        "desc": "Informações de ICMS",
                        "tipo": "object",
                        "obrigatorio": True,
                        "campos": {
                            "isento": {
                                "desc": "Indica se é isento de ICMS",
                                "tipo": "integer",
                                "obrigatorio": True,
                                "valores": [0, 1],
                                "formato": "0 = Não isento, 1 = Isento"
                            },
                            "aliq": {
                                "desc": "Alíquota de ICMS",
                                "tipo": "number",
                                "obrigatorio": True,
                                "formato": "Número decimal com 2 casas decimais"
                            },
                            "valor": {
                                "desc": "Valor do ICMS",
                                "tipo": "number",
                                "obrigatorio": True,
                                "formato": "Número decimal com 2 casas decimais"
                            },
                            "cst": {
                                "desc": "Código de Situação Tributária do ICMS",
                                "tipo": "string",
                                "tamanho": 3,
                                "obrigatorio": True,
                                "formato": "Código CST conforme legislação fiscal"
                            },
                            "subsTrib": {
                                "desc": "Informações de substituição tributária",
                                "tipo": "object",
                                "obrigatorio": True,
                                "campos": {
                                    "valor": {
                                        "desc": "Valor da substituição tributária",
                                        "tipo": "number",
                                        "obrigatorio": True,
                                        "formato": "Número decimal com 2 casas decimais"
                                    },
                                    "embutidoPreco": {
                                        "desc": "Indica se o valor da ST está embutido no preço",
                                        "tipo": "integer",
                                        "obrigatorio": True,
                                        "valores": [0, 1],
                                        "formato": "0 = Não embutido, 1 = Embutido"
                                    },
                                    "cest": {
                                        "desc": "Código CEST",
                                        "tipo": "string",
                                        "tamanho": 7,
                                        "obrigatorio": True,
                                        "formato": "Código CEST conforme legislação fiscal"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "vendasDevolucoesCancelamentos": {
        "desc": "Lista de devoluções/cancelamentos de vendas",
        "tipo": "array",
        "obrigatorio": True,
        "campos": {
            "codEstab": {
                "desc": "Código do estabelecimento",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "Alfa-numérico, deve existir em estabelecimentos.cod"
            },
            "codCliente": {
                "desc": "Código do cliente",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "Alfa-numérico, deve existir em clientes.cod"
            },
            "codProfSaude": {
                "desc": "Código do profissional de saúde",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "Alfa-numérico, deve existir em profissionaisSaude.cod"
            },
            "codProd": {
                "desc": "Código do produto",
                "tipo": "string",
                "tamanho": 13,
                "obrigatorio": True,
                "formato": "Alfa-numérico, deve existir em produtos.cod"
            },
            "comPrescricao": {
                "desc": "Venda original com prescrição",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [0, 1],
                "formato": "0 = Sem prescrição, 1 = Com prescrição"
            },
            "ecommerce": {
                "desc": "Venda original por e-commerce",
                "tipo": "integer",
                "obrigatorio": True,
                "valores": [0, 1],
                "formato": "0 = Não, 1 = Sim"
            },
            "dt": {
                "desc": "Data da devolução/cancelamento",
                "tipo": "string",
                "tamanho": 10,
                "obrigatorio": True,
                "formato": "YYYY-MM-DD"
            },
            "qt": {
                "desc": "Quantidade devolvida/cancelada",
                "tipo": "integer",
                "obrigatorio": True,
                "formato": "Número inteiro positivo"
            }
        }
    },
    "estoque": {
        "desc": "Lista de estoques",
        "tipo": "array",
        "obrigatorio": True,
        "campos": {
            "codEstab": {
                "desc": "Código do estabelecimento",
                "tipo": "string",
                "tamanho": 14,
                "obrigatorio": True,
                "formato": "Alfa-numérico, deve existir em estabelecimentos.cod"
            },
            "codProd": {
                "desc": "Código do produto",
                "tipo": "string",
                "tamanho": 13,
                "obrigatorio": True,
                "formato": "Alfa-numérico, deve existir em produtos.cod"
            },
            "dt": {
                "desc": "Data do estoque",
                "tipo": "string",
                "tamanho": 10,
                "obrigatorio": True,
                "formato": "YYYY-MM-DD"
            },
            "qt": {
                "desc": "Quantidade em estoque",
                "tipo": "integer",
                "obrigatorio": True,
                "formato": "Número inteiro positivo"
            }
        }
    }
}

def get_field_description(section: str, field: str) -> Optional[Dict[str, Any]]:
    """
    Retorna descrição de um campo específico.
    
    Args:
        section: Nome da seção (ex: 'estabelecimentos', 'clientes', etc.)
        field: Nome do campo (ex: 'cod', 'nome', etc.)
        
    Returns:
        Dicionário com a descrição do campo ou None se não encontrado
    """
    if section in IQVIA_DATA_DICTIONARY:
        section_dict = IQVIA_DATA_DICTIONARY[section]
        if 'campos' in section_dict and field in section_dict['campos']:
            return section_dict['campos'][field]
    return None

def get_section_description(section: str) -> Optional[Dict[str, Any]]:
    """
    Retorna descrição de uma seção específica.
    
    Args:
        section: Nome da seção (ex: 'estabelecimentos', 'clientes', etc.)
        
    Returns:
        Dicionário com a descrição da seção ou None se não encontrado
    """
    if section in IQVIA_DATA_DICTIONARY:
        return IQVIA_DATA_DICTIONARY[section]
    return None

def get_required_sections() -> List[str]:
    """
    Retorna lista de seções obrigatórias no layout IQVIA.
    
    Returns:
        Lista de nomes das seções obrigatórias
    """
    required = []
    for section, info in IQVIA_DATA_DICTIONARY.items():
        if info.get('obrigatorio', False):
            required.append(section)
    return required

def get_field_validation_info(section: str, field: str) -> Dict[str, Any]:
    """
    Retorna informações de validação para um campo específico.
    
    Args:
        section: Nome da seção (ex: 'estabelecimentos', 'clientes', etc.)
        field: Nome do campo (ex: 'cod', 'nome', etc.)
        
    Returns:
        Dicionário com informações de validação ou dicionário vazio se não encontrado
    """
    field_info = get_field_description(section, field)
    if not field_info:
        return {}
    
    validation = {
        'required': field_info.get('obrigatorio', False),
        'type': field_info.get('tipo', 'string')
    }
    
    if 'tamanho' in field_info:
        validation['max_length'] = field_info['tamanho']
    
    if 'valores' in field_info:
        validation['allowed_values'] = field_info['valores']
    
    if 'formato' in field_info:
        validation['format'] = field_info['formato']
    
    return validation