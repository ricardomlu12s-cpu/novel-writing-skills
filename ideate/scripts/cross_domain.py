#!/usr/bin/env python3
"""把一段情节压成一句话骨架，再随机套一个别的领域的词，撞出新点子。

比如「责任觉醒」这个骨架，套上「债务」「共生」这种不搭的词，会撞出
「主角继承的不是财产，是上一代的债」这种新方向。

用法:
  python3 cross_domain.py --skeleton "责任觉醒" --n 5
  python3 cross_domain.py --skeleton "责任觉醒" --graph --n 5   # 图模式，要装 networkx
"""
import argparse
import random
import sys

# 内置概念库(领域 -> 概念),完整版见 references/concept-bank.md
CONCEPT_BANK = {
    "宇宙物理": ["热寂", "熵增", "奇点", "量子纠缠", "多世界", "引力时间膨胀", "视界"],
    "生物生态": ["共生", "寄生", "群集智能", "灭绝与更替", "共生菌群", "宿主谈判"],
    "经济交易": ["债务继承", "契约", "通胀", "杠杆", "套利", "信用崩塌", "时间贴现"],
    "博弈棋": ["残局", "弃子", "双活", "读秒", "陷阱", "不败之地", "将军"],
    "法律契约": ["遗产", "担保", "违约责任", "信托", "衡平", "不可抗力"],
    "信息网络": ["熵", "信道", "压缩", "冗余", "噪声", "共识", "拜占庭将军"],
    "地质水文": ["侵蚀", "沉积", "地壳应力", "暗河", "涨落", "断崖"],
    "化学材料": ["催化", "晶格缺陷", "相变", "活性位点", "自修复"],
    "医学生理": ["免疫", "代偿", "过敏", "慢性炎症", "神经重塑", "成瘾与耐受"],
    "音乐声学": ["不协和音", "留白", "切分", "泛音", "共振", "跑调"],
    "建筑结构": ["承重墙", "拱", "悬臂", "地基", "抗震缝", "轻质化"],
    "农业节气": ["轮作", "休耕", "嫁接", "抽穗", "灌浆", "霜冻"],
    "航海天文": ["领航", "偏航", "风切变", "赤道无风带", "恒星导航", "潮汐锁定"],
    "语言修辞": ["隐喻", "转喻", "反讽", "留白", "复调", "陌生化"],
    "戏剧叙事": ["第四面墙", "麦高芬", "契诃夫之枪", "逆转", "镜像结构", "降神"],
    "军事战略": ["佯攻", "纵深", "补给线", "焦土", "斩首", "围点打援"],
    "心理认知": ["习得性无助", "认知失调", "峰终定律", "心流", "创伤后成长", "否认"],
    "宗教仪式": ["献祭", "赎罪", "轮回", "圣愚", "末世", "顿悟"],
    "体育竞技": ["体能分配", "抢开局", "田忌赛马", "黑马", "绝杀", "让球"],
    "美食感官": ["回甘", "层次", "火候", "断生", "锅气", "食材本味"],
}

# 骨架的领域归类(用于选"远邻"领域: 骨架属"成长"类,就选"宇宙/经济/生物"类)
SKELETON_DOMAIN_GUESS = {
    "成长": ["成长", "觉醒", "觉醒", "救赎", "蜕变", "和解", "责任", "守护", "选择", "代价"],
    "权力": ["权力", "争夺", "复仇", "算计", "权谋", "背叛", "上位"],
    "情感": ["爱情", "羁绊", "亲情", "遗憾", "错过", "守护", "依恋"],
}


def skeleton_domain(skeleton):
    for domain, kws in SKELETON_DOMAIN_GUESS.items():
        if any(kw in skeleton for kw in kws):
            return domain
    return None


def far_domains(skel_domain):
    """返回离骨架领域最远的几个领域(远邻联想)。"""
    if skel_domain == "成长":
        return ["经济交易", "宇宙物理", "生物生态", "信息网络", "地质水文"]
    if skel_domain == "权力":
        return ["医学生理", "音乐声学", "美食感官", "生物生态", "农业节气"]
    if skel_domain == "情感":
        return ["宇宙物理", "信息网络", "化学材料", "博弈棋", "建筑结构"]
    # 未知骨架领域 → 全库随机
    return list(CONCEPT_BANK.keys())


def pick_concepts(skel_domain, n, use_graph):
    concepts = []
    if use_graph:
        concepts = graph_neighbors(skel_domain, n)
    else:
        far = far_domains(skel_domain)
        # 从远邻领域各取 1 个概念
        chosen_domains = random.sample(far, min(n, len(far)))
        for d in chosen_domains:
            c = random.choice(CONCEPT_BANK[d])
            concepts.append((d, c))
    return concepts


def graph_neighbors(skel_domain, n):
    """用 networkx 从概念图随机游走取远邻(2-3 跳外)。无 networkx 时降级。"""
    try:
        import networkx as nx
    except ImportError:
        print(" 未安装 networkx,降级为内置概念库随机。安装: pip install networkx")
        return pick_concepts(skel_domain, n, use_graph=False)

    # 建图: 领域为节点,概念为边?简化为: 领域节点全连接,随机游走
    G = nx.Graph()
    domains = list(CONCEPT_BANK.keys())
    for d in domains:
        G.add_node(d)
    for i in range(len(domains)):
        for j in range(i + 1, len(domains)):
            G.add_edge(domains[i], domains[j])

    # 从骨架领域出发随机游走 3 步,落到远邻领域
    out = []
    start = skel_domain if skel_domain in domains else random.choice(domains)
    for _ in range(n):
        node = start
        for _ in range(3):  # 3 跳 = 远邻
            neighbors = list(G.neighbors(node))
            node = random.choice(neighbors)
        c = random.choice(CONCEPT_BANK[node])
        out.append((node, c))
    return out


def generate(skeleton, concepts):
    print(f"骨架: {skeleton}\n" + "=" * 60)
    print(f"嫁接候选({len(concepts)} 个):\n")
    for i, (domain, concept) in enumerate(concepts, 1):
        print(f"{i}. 【{skeleton} × {concept}】(来自: {domain})")
        print(f"   新方向: 把「{skeleton}」这个结构,用「{concept}」的机制重新演绎。")
        print(f"   → 例: 主角的{skeleton}不是继承/获得,而是{concept}。\n")
    print("=" * 60)
    print("提示: 这些是候选,不是定稿。逐个过常识矩阵 + 世界守恒三问 + 反套路库,留 1-2 个。")


def main():
    p = argparse.ArgumentParser(description="跨域联想")
    p.add_argument("--skeleton", required=True, help="情节骨架(去细节结构,如 责任觉醒)")
    p.add_argument("--n", type=int, default=5, help="生成候选数")
    p.add_argument("--graph", action="store_true", help="用图随机游走(需 networkx)")
    args = p.parse_args()

    sd = skeleton_domain(args.skeleton)
    concepts = pick_concepts(sd, args.n, args.graph)
    generate(args.skeleton, concepts)


if __name__ == "__main__":
    main()
