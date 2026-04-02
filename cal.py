import sys

def calculate_multi_inflow(inflows, total_earnings):
    """
    inflows: 列表，每个元素为 (天数, 本金)
    total_earnings: 总收益额
    """
    # 1. 计算总加权本金 (每一分钱存了多少天)
    # 比如 100块存3天，等效于 300块存1天
    weighted_principal_sum = sum(p * d for d, p in inflows)
    
    # 2. 计算日均本金 (假设总观察周期为所有投入中最长的那个天数，或者简单以加权法折算)
    # 金融机构常用：总收益 / (各笔本金 * 各自天数 / 365) 的求和
    # 简单年化公式：收益 / ( Σ(本金_i * 天数_i) / 365 )
    if weighted_principal_sum == 0:
        return
    
    annual_rate = (total_earnings * 365 / weighted_principal_sum) * 100
    
    # 3. 计算总投入本金
    total_principal = sum(p for d, p in inflows)

    print("-" * 40)
    print(f"{'投入序号':<10}{'本金':<15}{'持有天数':<10}")
    for i, (d, p) in enumerate(inflows, 1):
        print(f"{i:<12}{p:<17,.2f}{d:<10}")
    
    print("-" * 40)
    print(f"累计总投入:    {total_principal:,.2f}")
    print(f"累计总收益:    {total_earnings:,.2f}")
    print(f"加权年化率:    {annual_rate:.2f}% (基于日均本金)")
    print("-" * 40)

if __name__ == "__main__":
    # 参数格式：python script.py 天数1:本金1 天数2:本金2 ... 总收益
    # 示例：python script.py 30:5000 60:10000 200
    args = sys.argv[1:]
    if len(args) < 2:
        print("使用说明: python script.py [天数:本金] [天数:本金] ... [总收益]")
        print("示例: python script.py 30:5000 90:10000 500")
        sys.exit()

    try:
        total_earnings = float(args[-1])
        inflow_data = []
        for pair in args[:-1]:
            d, p = pair.split(":")
            inflow_data.append((int(d), float(p)))
        
        calculate_multi_inflow(inflow_data, total_earnings)
    except Exception as e:
        print(f"输入格式错误: {e}")

# 安盈理财32 279:10000 246:20000  217:10000 57:15000 387:8000 664.66 1.75
# 光大理财阳光金创稳健乐享日开90 394:10000 198.98 1.84
# 交银理财灵动慧利日开1号 541:10000 241.7 1.63
# 招银理财招睿和 94:10000 51.85 2.01
# 民生理财富竹固收91 27:10000 4:20000 20.38 2.13
# 招银理财招睿和添利270天持有期1A 454:20000 410.09 1.65
# 招银理财丰润180天2号F 582:20000 628.65 1.97 
# 10W 397:50000 369:20000 364:13000 311:10000 249:7000 2013.15 2.00