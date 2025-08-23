# -*- coding: utf-8 -*-
"""
Script para verificar a estrutura das tabelas principais
"""

from aurora_iqvia.db import AppConfig, connect_oracle

def verificar_estrutura_tabelas():
    """Verifica estrutura das tabelas principais"""
    
    print("🔍 VERIFICANDO ESTRUTURA DAS TABELAS")
    print("=" * 50)
    
    cfg = AppConfig.load()
    
    try:
        print("🔌 Conectando ao Oracle...")
        conn = connect_oracle(cfg)
        print(f"✅ Conectado: {conn.version}")
        
        cur = conn.cursor()
        
        # Lista de tabelas para verificar
        tabelas = [
            ('PCPRODUT', 'Produtos'),
            ('PCMOV', 'Movimentação'),
            ('PCNFSAID', 'Notas Fiscais Saída'),
            ('PCMOVCOMPLE', 'Complemento Movimento')
        ]
        
        for tabela, descricao in tabelas:
            print(f"\n📋 TABELA: {tabela} ({descricao})")
            print("-" * 40)
            
            try:
                # Buscar colunas da tabela
                cur.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
                    FROM USER_TAB_COLUMNS 
                    WHERE TABLE_NAME = :tabela
                    ORDER BY COLUMN_ID
                """, {'tabela': tabela})
                
                colunas = cur.fetchall()
                
                if colunas:
                    print(f"✅ {len(colunas)} colunas encontradas:")
                    
                    # Buscar colunas relacionadas a preço
                    colunas_preco = [col for col in colunas if 'PRECO' in col[0] or 'PTAB' in col[0] or 'VALOR' in col[0] or 'VL' in col[0]]
                    
                    if colunas_preco:
                        print("\n💰 Colunas relacionadas a PREÇO:")
                        for col in colunas_preco:
                            print(f"   - {col[0]} ({col[1]})")
                    
                    # Buscar colunas específicas importantes
                    colunas_importantes = []
                    campos_busca = ['CODPROD', 'CODAUXILIAR', 'DESCRICAO', 'PUNIT', 'QT', 'NUMNOTA']
                    
                    for campo in campos_busca:
                        col_encontrada = [col for col in colunas if campo in col[0]]
                        colunas_importantes.extend(col_encontrada)
                    
                    if colunas_importantes:
                        print("\n🔍 Colunas importantes encontradas:")
                        for col in colunas_importantes:
                            print(f"   - {col[0]} ({col[1]})")
                
                else:
                    print("❌ Tabela não encontrada ou sem acesso")
                    
            except Exception as e:
                print(f"❌ Erro ao consultar {tabela}: {e}")
        
        # Teste específico para preço de produto
        print("\n💰 TESTE ESPECÍFICO: Preços de Produtos")
        print("-" * 40)
        
        try:
            # Tentar diferentes campos de preço
            campos_preco = [
                'PVENDA',
                'PRECOREVENDA', 
                'PRECOVENDA',
                'PTABELA',
                'PRECOPROMOCAO',
                'CUSTOFIN'
            ]
            
            for campo in campos_preco:
                try:
                    cur.execute(f"SELECT {campo} FROM PRISMA.PCPRODUT WHERE ROWNUM = 1")
                    resultado = cur.fetchone()
                    if resultado is not None:
                        print(f"   ✅ {campo}: {resultado[0]} (DISPONÍVEL)")
                except:
                    print(f"   ❌ {campo}: NÃO DISPONÍVEL")
        
        except Exception as e:
            print(f"❌ Erro no teste de preços: {e}")
        
        # Teste específico para movimentação
        print("\n📦 TESTE ESPECÍFICO: Movimentação")
        print("-" * 40)
        
        try:
            cur.execute("""
                SELECT M.CODPROD, M.PUNIT, M.QT
                FROM PRISMA.PCMOV M 
                WHERE ROWNUM <= 3
                AND M.PUNIT IS NOT NULL
            """)
            
            movs = cur.fetchall()
            if movs:
                print("✅ Dados de movimentação encontrados:")
                for mov in movs:
                    print(f"   - Produto: {mov[0]}, Preço Unit: {mov[1]}, Qtd: {mov[2]}")
            else:
                print("⚠️ Nenhuma movimentação com preço encontrada")
                
        except Exception as e:
            print(f"❌ Erro no teste de movimentação: {e}")
        
        print("\n✅ VERIFICAÇÃO CONCLUÍDA")
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
    finally:
        try:
            conn.close()
            print("🔌 Conexão fechada")
        except:
            pass

if __name__ == "__main__":
    verificar_estrutura_tabelas()