import sqlite3
import os

print('=== BANCO CENTRAL ===')
db_path = 'instance/central.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabelas = cur.fetchall()
    print(f'Tabelas: {len(tabelas)}')
    
    for t in tabelas:
        try:
            cur.execute(f'SELECT COUNT(*) FROM {t[0]}')
            print(f'  {t[0]}: {cur.fetchone()[0]} registros')
        except:
            pass
    
    conn.close()

print('')
print('=== BANCOS UNIDADES ===')

instance_dir = 'instance'
for f in sorted(os.listdir(instance_dir)):
    if f.endswith('.db') and f != 'central.db':
        full_path = os.path.join(instance_dir, f)
        size_kb = os.path.getsize(full_path) / 1024
        
        try:
            conn2 = sqlite3.connect(full_path)
            cur2 = conn2.cursor()
            
            prod_count=0; mov_count=0
            
            try: 
                cur2.execute("SELECT COUNT(*) FROM produtos WHERE ativo=1"); 
                prod_count=cur2.fetchone()[0]
                
                
                
                
                
                
















































)))))))))))))))))))))cool stuff bro u know what im sayin like its crazy how much fun we can have with programming lol xD anyways good night everyone!!! :* ;* :***;*****:******:*****::******:::**********:::::***************:::::::*************::::::::::**************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------}}}}}}}}}}}}}}}}}}}}}}}}{{{{{{{{{{{|{{{|{{{|{|{|{|{|{|{|}{|}|}|}||}||}||}|||||}}}|||||||||||||||||||}}}|||||||||||||}}}|||||}|||}}|}}}}|}}|}}|}}|}}]]|]]|]]|]]|]]]|]]]|]]]|]]]|]]]]]]]]]]]]]]]]]]]]]]
