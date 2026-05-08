#!/usr/bin/env python3
"""
跨系统数据收集管道
目标：收集多种随机系统的数据进行统一分析

数据源：
1. HKJC Mark Six - 历史彩票数据
2. 金融市场 - 股票价格序列
3. PRNG - 伪随机数生成器
4. QRNG - 量子随机数生成器
5. 气象数据 - 温度/气压序列
"""

import os
import json
import sqlite3
import urllib.request
import ssl
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============ 配置 ============

OUTPUT_DIR = os.path.expanduser("~/.hermes/projects/M615042026-B/data/cross_system")
os.makedirs(OUTPUT_DIR, exist_ok=True)

MANIFEST_FILE = f"{OUTPUT_DIR}/MANIFEST.json"

# ============ 数据源定义 ============

DATA_SOURCES = {
    "hkjc_marksix": {
        "name": "HKJC Mark Six",
        "type": "Physical",
        "description": "香港马会彩票开奖号码",
        "url": "https://bet.hkjc.com/marksix/winning-numbers.aspx",
        "format": "CSV",
        "priority": "P0",
        "status": "pending"
    },
    "yahoo_finance": {
        "name": "Yahoo Finance",
        "type": "Chaotic",
        "description": "股票市场价格序列",
        "symbols": ["^HSI", "^AAPL", "BTC-USD"],
        "format": "JSON",
        "priority": "P1",
        "status": "pending"
    },
    "prng_random": {
        "name": "Python PRNG",
        "type": "Pseudorandom",
        "description": "Python 内置伪随机数生成器",
        "algorithms": ["random", "secrets", "urandom"],
        "format": "Binary",
        "priority": "P1",
        "status": "pending"
    },
    "qrng_random": {
        "name": "QRNG API",
        "type": "Quantum",
        "description": "量子随机数生成器API",
        "url": "https://qrng.ethz.ch/",
        "format": "JSON",
        "priority": "P2",
        "status": "pending"
    }
}

# ============ 数据收集函数 ============

def collect_hkjc_marksix():
    """
    收集 HKJC Mark Six 数据
    尝试多个数据源
    """
    print("\n[1/4] 收集 HKJC Mark Six 数据...")
    
    # 尝试从本地数据库查找
    db_paths = [
        os.path.expanduser("~/.hermes/hermes.db"),
        os.path.expanduser("~/.hermes/sessions.db"),
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 尝试查找相关表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0].lower()
                    if 'marksix' in table_name or 'lottery' in table_name or 'draw' in table_name:
                        cursor.execute(f"SELECT * FROM {table[0]} LIMIT 5")
                        rows = cursor.fetchall()
                        if rows:
                            print(f"找到数据表: {table[0]}")
                            conn.close()
                            return {"source": db_path, "table": table[0], "rows": len(rows)}
                
                conn.close()
            except Exception as e:
                print(f"检查 {db_path} 失败: {e}")
    
    # 尝试从网络获取
    try:
        context = ssl._create_unverified_context()
        url = "https://www.lotto.qc.com/en/ Publications /Lotto-6-49-winning-numbers.csv"
        # 使用备用数据源
        url = "https://raw.githubusercontent.com/expersso/hk-marksix/master/marksix.csv"
        
        with urllib.request.urlopen(url, timeout=10, context=context) as response:
            data = response.read().decode('utf-8')
            
        # 保存数据
        output_file = f"{OUTPUT_DIR}/hkjc_marksix.csv"
        with open(output_file, 'w') as f:
            f.write(data)
        
        lines = data.strip().split('\n')
        print(f"✓ HKJC Mark Six: {len(lines)} 行数据已保存")
        
        return {"source": url, "file": output_file, "rows": len(lines)}
        
    except Exception as e:
        print(f"✗ 网络获取失败: {e}")
        print("  需要手动下载 HKJC 数据")
        
        # 创建示例数据结构
        sample_file = f"{OUTPUT_DIR}/hkjc_marksix_sample.csv"
        with open(sample_file, 'w') as f:
            f.write("draw_no,date,ball_1,ball_2,ball_3,ball_4,ball_5,ball_6,extra\n")
            f.write("#需要从 HKJC 官网手动下载数据\n")
        
        return {"source": "pending", "note": "需要手动下载"}

def collect_yahoo_finance():
    """
    收集金融市场数据
    使用 Yahoo Finance API (yfinance)
    """
    print("\n[2/4] 收集金融市场数据...")
    
    try:
        import yfinance as yf
        
        symbols = ["^HSI", "^AAPL", "BTC-USD", "EURUSD=X"]
        results = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2y")  # 2年历史数据
                
                if len(hist) > 100:
                    # 保存为 CSV
                    output_file = f"{OUTPUT_DIR}/finance_{symbol.replace('^', '').replace('-', '_')}.csv"
                    hist.to_csv(output_file)
                    
                    results[symbol] = {
                        "file": output_file,
                        "rows": len(hist),
                        "start": str(hist.index[0].date()),
                        "end": str(hist.index[-1].date())
                    }
                    print(f"✓ {symbol}: {len(hist)} 条记录")
                else:
                    print(f"✗ {symbol}: 数据不足")
                    
            except Exception as e:
                print(f"✗ {symbol} 获取失败: {e}")
        
        return results
        
    except ImportError:
        print("✗ yfinance 未安装，跳过金融市场数据")
        print("  安装命令: pip install yfinance")
        return {"error": "yfinance not installed"}

def collect_prng_data():
    """
    生成/收集 PRNG 数据
    """
    print("\n[3/4] 生成 PRNG 测试数据...")
    
    import random
    
    results = {}
    
    # 1. Python random (梅森旋转)
    print("生成 Python random 序列...")
    random.seed(42)  # 固定种子，可复现
    random_seq = [random.random() for _ in range(10000)]
    
    output_file = f"{OUTPUT_DIR}/prng_python_random.csv"
    with open(output_file, 'w') as f:
        f.write("index,value\n")
        for i, v in enumerate(random_seq):
            f.write(f"{i},{v}\n")
    
    results["python_random"] = {
        "file": output_file,
        "type": "Mersenne Twister",
        "rows": len(random_seq),
        "seed": 42
    }
    print(f"✓ Python random: {len(random_seq)} 条记录")
    
    # 2. secrets 模块 (密码学安全)
    print("生成 secrets 序列...")
    import secrets
    secrets_seq = [secrets.randbelow(1000) / 1000 for _ in range(10000)]
    
    output_file = f"{OUTPUT_DIR}/prng_secrets.csv"
    with open(output_file, 'w') as f:
        f.write("index,value\n")
        for i, v in enumerate(secrets_seq):
            f.write(f"{i},{v}\n")
    
    results["secrets"] = {
        "file": output_file,
        "type": "Cryptographically Secure",
        "rows": len(secrets_seq)
    }
    print(f"✓ secrets: {len(secrets_seq)} 条记录")
    
    # 3. /dev/urandom
    print("读取 /dev/urandom...")
    try:
        with open('/dev/urandom', 'rb') as f:
            urandom_bytes = f.read(10000)
        urandom_vals = [b / 255.0 for b in urandom_bytes]
        
        output_file = f"{OUTPUT_DIR}/prng_urandom.csv"
        with open(output_file, 'w') as f:
            f.write("index,value\n")
            for i, v in enumerate(urandom_vals):
                f.write(f"{i},{v}\n")
        
        results["urandom"] = {
            "file": output_file,
            "type": "OS Random",
            "rows": len(urandom_vals)
        }
        print(f"✓ /dev/urandom: {len(urandom_vals)} 条记录")
    except:
        print("✗ /dev/urandom 读取失败")
    
    return results

def collect_qrng_data():
    """
    收集量子随机数数据
    """
    print("\n[4/4] 收集量子随机数数据...")
    
    # 量子随机数 API
    qrng_urls = [
        ("https://qrng.ethz.ch/api/randbyte", "ETH Zurich QRNG"),
        ("https://random.org/cgi-bin/randbyte", "Random.org"),
    ]
    
    results = {}
    
    for url, name in qrng_urls:
        try:
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(url, timeout=10, context=context) as response:
                data = response.read()
            
            # 保存原始数据
            output_file = f"{OUTPUT_DIR}/qrng_{name.replace(' ', '_').lower()}.bin"
            with open(output_file, 'wb') as f:
                f.write(data)
            
            # 转换为可读格式
            vals = [b / 255.0 for b in data]
            
            csv_file = output_file.replace('.bin', '.csv')
            with open(csv_file, 'w') as f:
                f.write("index,value\n")
                for i, v in enumerate(vals):
                    f.write(f"{i},{v}\n")
            
            results[name] = {
                "file": csv_file,
                "type": "Quantum",
                "rows": len(vals),
                "source": url
            }
            print(f"✓ {name}: {len(vals)} 条量子随机数")
            
        except Exception as e:
            print(f"✗ {name} 获取失败: {e}")
    
    if not results:
        print("  创建 QRNG 占位符...")
        placeholder_file = f"{OUTPUT_DIR}/qrng_placeholder.txt"
        with open(placeholder_file, 'w') as f:
            f.write("# Quantum RNG data placeholder\n")
            f.write("# Available APIs:\n")
            f.write("# - https://qrng.ethz.ch/\n")
            f.write("# - https://api.random.org/\n")
        results["placeholder"] = {"file": placeholder_file}
    
    return results

# ============ 更新清单 ============

def update_manifest(all_results):
    """更新数据清单"""
    manifest = {
        "created": datetime.now().isoformat(),
        "sources": DATA_SOURCES,
        "collected": all_results,
        "summary": {
            "total_sources": len(DATA_SOURCES),
            "successful": sum(1 for r in all_results.values() if not r.get("error")),
            "failed": sum(1 for r in all_results.values() if r.get("error"))
        }
    }
    
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n清单已更新: {MANIFEST_FILE}")
    return manifest

# ============ 主函数 ============

def main():
    print("=" * 60)
    print("跨系统数据收集管道")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)
    
    results = {}
    
    # 1. HKJC Mark Six
    results["hkjc_marksix"] = collect_hkjc_marksix()
    
    # 2. 金融市场
    results["yahoo_finance"] = collect_yahoo_finance()
    
    # 3. PRNG
    results["prng"] = collect_prng_data()
    
    # 4. QRNG
    results["qrng"] = collect_qrng_data()
    
    # 更新清单
    manifest = update_manifest(results)
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("数据收集摘要")
    print("=" * 60)
    print(f"成功: {manifest['summary']['successful']}/{manifest['summary']['total_sources']}")
    print(f"失败: {manifest['summary']['failed']}")
    print(f"\n数据目录: {OUTPUT_DIR}")
    
    return results

if __name__ == "__main__":
    main()
