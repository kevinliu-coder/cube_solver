"""把 S=7 / S=9 的里程碑链, 按合理几何摆法用 UDLRFB 展开图画出来。
模型只给"角数/棱数", 这里指定具体块(自底向上顺序), 仅供直观。
"""
from stages import cornerFacelet, edgeFacelet, EMOJI

GRAY = "⬛"
CENTERS = {4:0,13:1,22:2,31:3,40:4,49:5}

# 自底向上的解块顺序(可改; 仅为几何直观)
CORNER_ORDER = [5,6,4,7, 1,0,2,3]      # DLF DBL DFR DRB, UFL URF ULB UBR
EDGE_ORDER   = [5,7,6,4, 9,8,11,10, 1,3,2,0]  # DF DB DL DR, FL FR BR BL, UF UB UL UR

def mask_for(nc, ne):
    m=dict(CENTERS)
    for i in CORNER_ORDER[:nc]:
        for f in cornerFacelet[i]: m[f]=f//9
    for j in EDGE_ORDER[:ne]:
        for f in edgeFacelet[j]: m[f]=f//9
    return m

def net(m):
    def cell(i): return EMOJI[m[i]] if i in m else GRAY
    def row(face,r): return "".join(cell(face*9+r*3+col) for col in range(3))
    pad="      "; L=[]
    for r in range(3): L.append(pad+row(0,r))
    for r in range(3): L.append(row(4,r)+" "+row(2,r)+" "+row(1,r)+" "+row(5,r))
    for r in range(3): L.append(pad+row(3,r))
    return "\n".join(L)

CHAINS = {
 "S=7 (4阶段, 46步)": [(0,2),(3,4),(8,6),(8,12)],
 "S=9 (3阶段, 43步)": [(0,1),(8,3),(8,12)],
}

if __name__=="__main__":
    for name, ms in CHAINS.items():
        print("="*30, name, "="*5, "\n")
        for i,(nc,ne) in enumerate(ms):
            print(f"里程碑{i+1}: 已解 {nc}角 {ne}棱")
            print(net(mask_for(nc,ne)))
            print()
