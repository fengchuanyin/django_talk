import time
import pandas as pd
from DrissionPage import ChromiumPage, ChromiumOptions

def crawl_jd_iqoo15_reviews(product_id, target_count=50):
    # --- 1. 浏览器初始化 ---
    co = ChromiumOptions()
    # 【注意】请确认这是你电脑上 Chrome 的真实路径
    co.set_browser_path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe') 
    page = ChromiumPage(co)
    
    try:
        # --- 2. 访问页面并进入评价弹窗 ---
        url = f'https://item.jd.com/{product_id}.html'
        page.get(url)
        print(f"正在打开商品 {product_id} ...")
        
        # 向下滚动以加载“全部评价”按钮所在的区域
        page.scroll.down(1500)
        time.sleep(1.5)
        
        # 点击截图中的“全部评价 >”按钮
        btn = page.ele('text=全部评价')
        if btn:
            btn.click(by_js=True)
            print("已点击『全部评价』，进入弹窗模式...")
            time.sleep(2)
        else:
            print("未找到点击按钮，请检查页面是否已发生变化。")
            return

        # --- 3. 循环滚动抓取（适配虚拟滚动） ---
        all_comments = []
        seen_ids = set()  # 用于去重
        
        print(f"开始采集，目标数量：{target_count} 条...")
        
        while len(all_comments) < target_count:
            # 获取当前 DOM 中所有可见的评价卡片
            cards = page.eles('css:.jdc-pc-rate-card')
            
            for card in cards:
                try:
                    # 提取昵称
                    nick = card.ele('css:.jdc-pc-rate-card-nick').text
                    # 提取评价正文
                    content = card.ele('css:.jdc-pc-rate-card-main-desc').text
                    
                    # 生成去重 ID（昵称 + 内容前15字）
                    comment_id = f"{nick}_{content[:15]}"
                    
                    if comment_id not in seen_ids:
                        # 提取规格和日期
                        info_left = card.ele('css:.jdc-pc-rate-card-info-left')
                        date = info_left.ele('css:.date').text if info_left.ele('css:.date') else ""
                        spec = info_left.ele('css:.info').text if info_left.ele('css:.info') else ""
                        
                        # 提取追评（截图中的红色字样）
                        after_ele = card.ele('css:.jdc-pc-rate-card-after', timeout=0.1)
                        after_comment = after_ele.text if after_ele else ""
                        
                        # 提取商家回复
                        reply_ele = card.ele('css:.jdc-pc-rate-card-reply', timeout=0.1)
                        reply = reply_ele.text.replace('商家回复：', '') if reply_ele else ""

                        all_comments.append({
                            "序号": len(all_comments) + 1,
                            "用户昵称": nick,
                            "评价日期": date,
                            "购买规格": spec,
                            "评价内容": content.replace('\n', ' '),
                            "追加评论": after_comment.replace('\n', ' '),
                            "商家回复": reply.replace('\n', ' ')
                        })
                        seen_ids.add(comment_id)
                        
                        if len(all_comments) >= target_count:
                            break
                except:
                    continue

            if len(all_comments) >= target_count:
                break
                
            # --- 滚动逻辑 ---
            # 找到最后一个卡片并滚动到它，触发虚拟列表加载
            if cards:
                cards[-1].scroll.to_see()
                print(f"当前已采集 {len(all_comments)} 条...")
                time.sleep(1.5) # 适当延迟模拟真人，防止被封
            else:
                # 如果没找到卡片，强制操作弹窗内的滚动条
                page.run_js('document.querySelector(\'div[data-virtuoso-scroller="true"]\').scrollTop += 1000')
                time.sleep(2)

        # --- 4. 导出数据 ---
        df = pd.DataFrame(all_comments)
        file_name = f"jd_comments_{product_id}.xlsx"
        df.to_excel(file_name, index=False)
        print(f"\n采集完成！")
        print(f"总计提取：{len(all_comments)} 条唯一评价")
        print(f"保存路径：{file_name}")

    finally:
        # 爬取结束后不立即关闭浏览器，方便查看
        # page.quit()
        pass

if __name__ == "__main__":
    # 使用你指定的 SKU ID (vivo iQOO 15)
    crawl_jd_iqoo15_reviews('100283678024', 50)