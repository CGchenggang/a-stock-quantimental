{
  "as_of": "2026-09-07T09:01:56.574741",
  "date": "20260907",
  "pool_alerts": [
    {
      "type": "📋 持仓简化",
      "detail": "8/31清仓7只，仅保留兆易创新2手+中国巨石2手",
      "severity": "INFO"
    },
    {
      "type": "✅ 板块集中度合规",
      "detail": "半导体仅兆易1只(占比~50%)，其余为新材料。集中度大幅改善",
      "severity": "INFO"
    }
  ],
  "holdings": [
    {
      "ticker": "603986",
      "name": "兆易创新",
      "sector": "半导体/存储",
      "role": "spear",
      "ohlcv": {
        "open": 387.58,
        "high": 388.97,
        "low": 368.77,
        "close": 371.88,
        "volume": 29969135,
        "amount": null,
        "turnover": null,
        "pct": 0.0
      },
      "ma": {
        "ma5": 381.76,
        "ma10": 391.08,
        "ma20": 401.35,
        "ma60": 500.38
      },
      "lr": 0.75,
      "stop_loss": {
        "above_ma20": false,
        "lr_above_12": false,
        "trigger": false,
        "ma20_distance_pct": -7.34
      },
      "trend": {
        "is_trend": false,
        "strategy": "均值回归",
        "buy_signal": "等回调到MA20(401.35)",
        "stop_loss_ref": "MA20"
      },
      "error": null
    },
    {
      "ticker": "600176",
      "name": "中国巨石",
      "sector": "新材料/玻纤",
      "role": "shield",
      "ohlcv": {
        "open": 43.04,
        "high": 43.3,
        "low": 39.78,
        "close": 40.18,
        "volume": 216682250,
        "amount": null,
        "turnover": null,
        "pct": 0.0
      },
      "ma": {
        "ma5": 42.03,
        "ma10": 41.92,
        "ma20": 42.33,
        "ma60": 48.33
      },
      "lr": 0.95,
      "stop_loss": {
        "above_ma20": false,
        "lr_above_12": false,
        "trigger": false,
        "ma20_distance_pct": -5.08
      },
      "trend": {
        "is_trend": false,
        "strategy": "均值回归",
        "buy_signal": "等回调到MA20(42.33)",
        "stop_loss_ref": "MA20"
      },
      "error": null
    }
  ],
  "index_snapshot": {
    "ok": true,
    "indices": {
      "上证指数": {
        "price": 0.0,
        "prev_close": 3930.1164,
        "pct": -100.0
      },
      "创业板指": {
        "price": 0.0,
        "prev_close": 3286.546,
        "pct": -100.0
      },
      "沪深300": {
        "price": 0.0,
        "prev_close": 4548.0499,
        "pct": -100.0
      }
    },
    "error": null
  },
  "macro_context": {
    "us_treasury": {
      "us10y": 4.78,
      "us30y": 5.24,
      "us2y": 4.37
    },
    "usd": {
      "usd_cnh": 6.7787,
      "source": "BOC via data_layer",
      "dxy_note": "需 AI WebSearch 补充（搜索 DXY 美元指数）"
    },
    "a50_futures": {
      "price": 14708.72,
      "pct": 0.38,
      "date": "2026-09-07",
      "name": "富时中国A50期货",
      "source": "sina_hf_CHA50CFD"
    },
    "northbound": {
      "deprecated": "2024-08起停止披露每日北向净额; 主力资金见 individual_fund_flow/sector_fund_flow"
    },
    "commodities": {},
    "sox": {
      "price": 11735.26,
      "pct": 3.37,
      "date": "2026-09-04",
      "source": "akshare_index_us_stock_sina"
    },
    "us_market": {
      "stocks": {
        "NVDA": {
          "close": 230.36,
          "pct": 0.84,
          "date": "2026-09-04 00:00:00",
          "is_stale": false
        },
        "AMD": {
          "close": 477.57,
          "pct": 4.69,
          "date": "2026-09-04 00:00:00",
          "is_stale": false
        },
        "TSLA": {
          "close": 354.08,
          "pct": -5.92,
          "date": "2026-09-04 00:00:00",
          "is_stale": false
        }
      },
      "source": "data_layer"
    },
    "error": null
  },
  "individual_fund_flow": {
    "ok": false,
    "holdings_flow": [],
    "error": "个股资金流采集异常: Length mismatch: Expected axis has 13 elements, new values have 10 elements"
  },
  "sector_fund_flow": {
    "ok": true,
    "industry": [
      {
        "name": "养殖业",
        "pct": 4.36,
        "net_yi": 16.02,
        "inflow_yi": 54.33,
        "outflow_yi": 38.31,
        "rank": 1,
        "leader": "罗牛山",
        "leader_pct": 10.05,
        "company_count": 36.0
      },
      {
        "name": "农产品加工",
        "pct": 3.6,
        "net_yi": 9.77,
        "inflow_yi": 49.71,
        "outflow_yi": 39.94,
        "rank": 2,
        "leader": "播恩集团",
        "leader_pct": 10.04,
        "company_count": 43.0
      },
      {
        "name": "白酒",
        "pct": 2.87,
        "net_yi": 31.74,
        "inflow_yi": 79.29,
        "outflow_yi": 47.55,
        "rank": 3,
        "leader": "顺鑫农业",
        "leader_pct": 5.35,
        "company_count": 19.0
      },
      {
        "name": "种植业与林业",
        "pct": 2.48,
        "net_yi": 11.61,
        "inflow_yi": 60.88,
        "outflow_yi": 49.27,
        "rank": 4,
        "leader": "亚盛集团",
        "leader_pct": 10.1,
        "company_count": 30.0
      },
      {
        "name": "影视院线",
        "pct": 2.44,
        "net_yi": 7.8,
        "inflow_yi": 39.07,
        "outflow_yi": 31.28,
        "rank": 5,
        "leader": "欢瑞世纪",
        "leader_pct": 10.04,
        "company_count": 20.0
      },
      {
        "name": "文化传媒",
        "pct": 2.44,
        "net_yi": 28.93,
        "inflow_yi": 198.85,
        "outflow_yi": 169.92,
        "rank": 6,
        "leader": "易点天下",
        "leader_pct": 11.12,
        "company_count": 85.0
      },
      {
        "name": "饮料制造",
        "pct": 2.23,
        "net_yi": 4.31,
        "inflow_yi": 29.08,
        "outflow_yi": 24.77,
        "rank": 7,
        "leader": "古越龙山",
        "leader_pct": 10.06,
        "company_count": 47.0
      },
      {
        "name": "食品加工制造",
        "pct": 1.91,
        "net_yi": 1.34,
        "inflow_yi": 34.07,
        "outflow_yi": 32.73,
        "rank": 8,
        "leader": "安记食品",
        "leader_pct": 10.04,
        "company_count": 66.0
      },
      {
        "name": "游戏",
        "pct": 1.81,
        "net_yi": 24.52,
        "inflow_yi": 75.72,
        "outflow_yi": 51.2,
        "rank": 9,
        "leader": "世纪华通",
        "leader_pct": 7.96,
        "company_count": 23.0
      },
      {
        "name": "旅游及酒店",
        "pct": 1.47,
        "net_yi": 2.9,
        "inflow_yi": 25.52,
        "outflow_yi": 22.62,
        "rank": 10,
        "leader": "华天酒店",
        "leader_pct": 10.09,
        "company_count": 35.0
      },
      {
        "name": "软件开发",
        "pct": 1.31,
        "net_yi": 25.63,
        "inflow_yi": 181.9,
        "outflow_yi": 156.26,
        "rank": 11,
        "leader": "四方精创",
        "leader_pct": 14.58,
        "company_count": 138.0
      },
      {
        "name": "互联网电商",
        "pct": 1.26,
        "net_yi": -2.47,
        "inflow_yi": 20.78,
        "outflow_yi": 23.25,
        "rank": 12,
        "leader": "国联股份",
        "leader_pct": 9.36,
        "company_count": 20.0
      },
      {
        "name": "机场航运",
        "pct": 1.22,
        "net_yi": 6.39,
        "inflow_yi": 16.12,
        "outflow_yi": 9.73,
        "rank": 13,
        "leader": "海南机场",
        "leader_pct": 2.56,
        "company_count": 13.0
      },
      {
        "name": "医药商业",
        "pct": 1.19,
        "net_yi": 0.4,
        "inflow_yi": 12.38,
        "outflow_yi": 11.98,
        "rank": 14,
        "leader": "合富中国",
        "leader_pct": 9.98,
        "company_count": 32.0
      },
      {
        "name": "房地产",
        "pct": 1.18,
        "net_yi": -2.24,
        "inflow_yi": 68.75,
        "outflow_yi": 70.99,
        "rank": 15,
        "leader": "我爱我家",
        "leader_pct": 10.14,
        "company_count": 88.0
      },
      {
        "name": "多元金融",
        "pct": 1.07,
        "net_yi": 2.63,
        "inflow_yi": 31.16,
        "outflow_yi": 28.53,
        "rank": 16,
        "leader": "翠微股份",
        "leader_pct": 10.04,
        "company_count": 26.0
      },
      {
        "name": "贸易",
        "pct": 1.05,
        "net_yi": 0.47,
        "inflow_yi": 4.17,
        "outflow_yi": 3.7,
        "rank": 17,
        "leader": "远大控股",
        "leader_pct": 5.22,
        "company_count": 14.0
      },
      {
        "name": "军工装备",
        "pct": 0.94,
        "net_yi": 41.69,
        "inflow_yi": 187.76,
        "outflow_yi": 146.07,
        "rank": 18,
        "leader": "中国船舶",
        "leader_pct": 9.18,
        "company_count": 82.0
      },
      {
        "name": "零售",
        "pct": 0.89,
        "net_yi": 7.25,
        "inflow_yi": 67.33,
        "outflow_yi": 60.08,
        "rank": 19,
        "leader": "百大集团",
        "leader_pct": 9.98,
        "company_count": 71.0
      },
      {
        "name": "港口航运",
        "pct": 0.74,
        "net_yi": -3.89,
        "inflow_yi": 43.11,
        "outflow_yi": 47.0,
        "rank": 20,
        "leader": "海通发展",
        "leader_pct": 9.99,
        "company_count": 36.0
      },
      {
        "name": "证券",
        "pct": 0.73,
        "net_yi": 18.13,
        "inflow_yi": 137.85,
        "outflow_yi": 119.72,
        "rank": 21,
        "leader": "湘财股份",
        "leader_pct": 7.5,
        "company_count": 50.0
      },
      {
        "name": "美容护理",
        "pct": 0.71,
        "net_yi": 2.0,
        "inflow_yi": 11.22,
        "outflow_yi": 9.22,
        "rank": 22,
        "leader": "润本股份",
        "leader_pct": 4.5,
        "company_count": 34.0
      },
      {
        "name": "银行",
        "pct": 0.65,
        "net_yi": 15.25,
        "inflow_yi": 107.1,
        "outflow_yi": 91.86,
        "rank": 23,
        "leader": "浦发银行",
        "leader_pct": 1.73,
        "company_count": 84.0
      },
      {
        "name": "建筑装饰",
        "pct": 0.64,
        "net_yi": -4.15,
        "inflow_yi": 70.34,
        "outflow_yi": 74.49,
        "rank": 24,
        "leader": "华阳国际",
        "leader_pct": 10.01,
        "company_count": 143.0
      },
      {
        "name": "综合",
        "pct": 0.62,
        "net_yi": 0.54,
        "inflow_yi": 12.71,
        "outflow_yi": 12.17,
        "rank": 25,
        "leader": "上海三毛",
        "leader_pct": 7.11,
        "company_count": 18.0
      },
      {
        "name": "包装印刷",
        "pct": 0.62,
        "net_yi": -0.71,
        "inflow_yi": 23.89,
        "outflow_yi": 24.6,
        "rank": 26,
        "leader": "柏星龙",
        "leader_pct": 30.0,
        "company_count": 46.0
      },
      {
        "name": "汽车整车",
        "pct": 0.61,
        "net_yi": 2.75,
        "inflow_yi": 31.91,
        "outflow_yi": 29.16,
        "rank": 27,
        "leader": "中国重汽",
        "leader_pct": 2.67,
        "company_count": 23.0
      },
      {
        "name": "物流",
        "pct": 0.6,
        "net_yi": 3.74,
        "inflow_yi": 15.13,
        "outflow_yi": 11.39,
        "rank": 28,
        "leader": "密尔克卫",
        "leader_pct": 3.74,
        "company_count": 50.0
      },
      {
        "name": "油气开采及服务",
        "pct": 0.5,
        "net_yi": -0.68,
        "inflow_yi": 16.6,
        "outflow_yi": 17.28,
        "rank": 29,
        "leader": "博迈科",
        "leader_pct": 4.19,
        "company_count": 19.0
      },
      {
        "name": "家居用品",
        "pct": 0.48,
        "net_yi": 1.1,
        "inflow_yi": 29.15,
        "outflow_yi": 28.05,
        "rank": 30,
        "leader": "实丰文化",
        "leader_pct": 10.01,
        "company_count": 98.0
      },
      {
        "name": "公路铁路运输",
        "pct": 0.46,
        "net_yi": -3.55,
        "inflow_yi": 14.48,
        "outflow_yi": 18.04,
        "rank": 31,
        "leader": "深高速",
        "leader_pct": 3.54,
        "company_count": 32.0
      },
      {
        "name": "石油加工贸易",
        "pct": 0.41,
        "net_yi": 0.75,
        "inflow_yi": 22.09,
        "outflow_yi": 21.34,
        "rank": 32,
        "leader": "统一股份",
        "leader_pct": 10.01,
        "company_count": 27.0
      },
      {
        "name": "燃气",
        "pct": 0.36,
        "net_yi": -0.26,
        "inflow_yi": 10.25,
        "outflow_yi": 10.51,
        "rank": 33,
        "leader": "美能能源",
        "leader_pct": 2.99,
        "company_count": 27.0
      },
      {
        "name": "IT服务",
        "pct": 0.34,
        "net_yi": -13.6,
        "inflow_yi": 140.59,
        "outflow_yi": 154.19,
        "rank": 34,
        "leader": "海峡创新",
        "leader_pct": 16.01,
        "company_count": 129.0
      },
      {
        "name": "汽车服务及其他",
        "pct": 0.26,
        "net_yi": 0.04,
        "inflow_yi": 5.48,
        "outflow_yi": 5.44,
        "rank": 35,
        "leader": "ST中路",
        "leader_pct": 2.2,
        "company_count": 26.0
      },
      {
        "name": "电力",
        "pct": 0.19,
        "net_yi": -4.49,
        "inflow_yi": 93.48,
        "outflow_yi": 97.97,
        "rank": 36,
        "leader": "恒盛能源",
        "leader_pct": 9.98,
        "company_count": 110.0
      },
      {
        "name": "服装家纺",
        "pct": 0.19,
        "net_yi": 2.03,
        "inflow_yi": 30.01,
        "outflow_yi": 27.98,
        "rank": 37,
        "leader": "太湖雪",
        "leader_pct": 6.25,
        "company_count": 75.0
      },
      {
        "name": "其他社会服务",
        "pct": 0.17,
        "net_yi": -0.31,
        "inflow_yi": 13.32,
        "outflow_yi": 13.63,
        "rank": 38,
        "leader": "科锐国际",
        "leader_pct": 6.91,
        "company_count": 84.0
      },
      {
        "name": "小家电",
        "pct": 0.15,
        "net_yi": 0.92,
        "inflow_yi": 5.7,
        "outflow_yi": 4.78,
        "rank": 39,
        "leader": "爱仕达",
        "leader_pct": 10.05,
        "company_count": 26.0
      },
      {
        "name": "农化制品",
        "pct": 0.14,
        "net_yi": -1.23,
        "inflow_yi": 50.47,
        "outflow_yi": 51.7,
        "rank": 40,
        "leader": "利尔化学",
        "leader_pct": 3.48,
        "company_count": 61.0
      },
      {
        "name": "保险",
        "pct": 0.11,
        "net_yi": 0.17,
        "inflow_yi": 36.1,
        "outflow_yi": 35.93,
        "rank": 41,
        "leader": "新华保险",
        "leader_pct": 0.53,
        "company_count": 5.0
      },
      {
        "name": "教育",
        "pct": 0.04,
        "net_yi": -0.16,
        "inflow_yi": 9.78,
        "outflow_yi": 9.94,
        "rank": 42,
        "leader": "ST豆神",
        "leader_pct": 10.42,
        "company_count": 15.0
      },
      {
        "name": "轨交设备",
        "pct": 0.03,
        "net_yi": 0.62,
        "inflow_yi": 6.71,
        "outflow_yi": 6.09,
        "rank": 43,
        "leader": "ST朗进",
        "leader_pct": 4.28,
        "company_count": 30.0
      },
      {
        "name": "钢铁",
        "pct": 0.03,
        "net_yi": -1.05,
        "inflow_yi": 22.26,
        "outflow_yi": 23.3,
        "rank": 44,
        "leader": "鄂尔多斯",
        "leader_pct": 5.9,
        "company_count": 44.0
      },
      {
        "name": "工程机械",
        "pct": 0.02,
        "net_yi": 0.64,
        "inflow_yi": 18.92,
        "outflow_yi": 18.27,
        "rank": 45,
        "leader": "铁拓机械",
        "leader_pct": 9.65,
        "company_count": 36.0
      },
      {
        "name": "建筑材料",
        "pct": 0.01,
        "net_yi": -26.46,
        "inflow_yi": 66.35,
        "outflow_yi": 92.81,
        "rank": 46,
        "leader": "福建水泥",
        "leader_pct": 9.92,
        "company_count": 73.0
      },
      {
        "name": "医疗器械",
        "pct": -0.04,
        "net_yi": -0.01,
        "inflow_yi": 49.7,
        "outflow_yi": 49.71,
        "rank": 47,
        "leader": "可孚医疗",
        "leader_pct": 7.55,
        "company_count": 140.0
      },
      {
        "name": "中药",
        "pct": -0.07,
        "net_yi": -0.55,
        "inflow_yi": 25.93,
        "outflow_yi": 26.48,
        "rank": 48,
        "leader": "*ST香雪",
        "leader_pct": 4.29,
        "company_count": 68.0
      },
      {
        "name": "风电设备",
        "pct": -0.14,
        "net_yi": -3.73,
        "inflow_yi": 17.85,
        "outflow_yi": 21.59,
        "rank": 49,
        "leader": "电气风电",
        "leader_pct": 12.57,
        "company_count": 31.0
      },
      {
        "name": "电网设备",
        "pct": -0.15,
        "net_yi": -1.31,
        "inflow_yi": 142.27,
        "outflow_yi": 143.58,
        "rank": 50,
        "leader": "益坤电气",
        "leader_pct": 7.99,
        "company_count": 140.0
      },
      {
        "name": "光伏设备",
        "pct": -0.27,
        "net_yi": 1.16,
        "inflow_yi": 65.27,
        "outflow_yi": 64.11,
        "rank": 51,
        "leader": "欧普泰",
        "leader_pct": 3.95,
        "company_count": 73.0
      },
      {
        "name": "纺织制造",
        "pct": -0.33,
        "net_yi": -1.47,
        "inflow_yi": 4.98,
        "outflow_yi": 6.46,
        "rank": 52,
        "leader": "浔兴股份",
        "leader_pct": 2.44,
        "company_count": 33.0
      },
      {
        "name": "计算机设备",
        "pct": -0.35,
        "net_yi": -28.77,
        "inflow_yi": 118.46,
        "outflow_yi": 147.23,
        "rank": 53,
        "leader": "锐明技术",
        "leader_pct": 4.39,
        "company_count": 83.0
      },
      {
        "name": "厨卫电器",
        "pct": -0.42,
        "net_yi": 0.0,
        "inflow_yi": 4.07,
        "outflow_yi": 4.06,
        "rank": 54,
        "leader": "日出东方",
        "leader_pct": 3.03,
        "company_count": 9.0
      },
      {
        "name": "通信服务",
        "pct": -0.43,
        "net_yi": -3.93,
        "inflow_yi": 35.78,
        "outflow_yi": 39.71,
        "rank": 55,
        "leader": "世纪鼎利",
        "leader_pct": 2.09,
        "company_count": 44.0
      },
      {
        "name": "环境治理",
        "pct": -0.46,
        "net_yi": -9.32,
        "inflow_yi": 33.41,
        "outflow_yi": 42.73,
        "rank": 56,
        "leader": "南大环境",
        "leader_pct": 12.95,
        "company_count": 111.0
      },
      {
        "name": "化学制品",
        "pct": -0.49,
        "net_yi": -24.11,
        "inflow_yi": 105.55,
        "outflow_yi": 129.66,
        "rank": 57,
        "leader": "大禹生物",
        "leader_pct": 17.7,
        "company_count": 183.0
      },
      {
        "name": "造纸",
        "pct": -0.52,
        "net_yi": -2.51,
        "inflow_yi": 7.88,
        "outflow_yi": 10.38,
        "rank": 58,
        "leader": "宜宾纸业",
        "leader_pct": 1.26,
        "company_count": 24.0
      },
      {
        "name": "环保设备",
        "pct": -0.57,
        "net_yi": -1.99,
        "inflow_yi": 12.08,
        "outflow_yi": 14.07,
        "rank": 59,
        "leader": "紫金龙净",
        "leader_pct": 4.62,
        "company_count": 30.0
      },
      {
        "name": "白色家电",
        "pct": -0.59,
        "net_yi": -3.77,
        "inflow_yi": 35.22,
        "outflow_yi": 38.98,
        "rank": 60,
        "leader": "万朗磁塑",
        "leader_pct": 7.01,
        "company_count": 44.0
      },
      {
        "name": "化学制药",
        "pct": -0.6,
        "net_yi": -16.61,
        "inflow_yi": 104.31,
        "outflow_yi": 120.92,
        "rank": 61,
        "leader": "昂利康",
        "leader_pct": 6.12,
        "company_count": 158.0
      },
      {
        "name": "煤炭开采加工",
        "pct": -0.6,
        "net_yi": 0.48,
        "inflow_yi": 39.63,
        "outflow_yi": 39.15,
        "rank": 62,
        "leader": "晋控煤业",
        "leader_pct": 3.63,
        "company_count": 34.0
      },
      {
        "name": "医疗服务",
        "pct": -0.66,
        "net_yi": -2.02,
        "inflow_yi": 65.34,
        "outflow_yi": 67.36,
        "rank": 63,
        "leader": "诺思格",
        "leader_pct": 6.38,
        "company_count": 56.0
      },
      {
        "name": "化学纤维",
        "pct": -0.69,
        "net_yi": -3.9,
        "inflow_yi": 17.8,
        "outflow_yi": 21.71,
        "rank": 64,
        "leader": "吉林化纤",
        "leader_pct": 3.52,
        "company_count": 29.0
      },
      {
        "name": "其他电源设备",
        "pct": -0.72,
        "net_yi": -2.78,
        "inflow_yi": 50.79,
        "outflow_yi": 53.57,
        "rank": 65,
        "leader": "汽轮科技",
        "leader_pct": 6.91,
        "company_count": 35.0
      },
      {
        "name": "化学原料",
        "pct": -0.85,
        "net_yi": -11.82,
        "inflow_yi": 58.44,
        "outflow_yi": 70.26,
        "rank": 66,
        "leader": "振华股份",
        "leader_pct": 4.11,
        "company_count": 59.0
      },
      {
        "name": "专用设备",
        "pct": -0.9,
        "net_yi": -31.37,
        "inflow_yi": 123.38,
        "outflow_yi": 154.74,
        "rank": 67,
        "leader": "天沃科技",
        "leader_pct": 10.04,
        "company_count": 201.0
      },
      {
        "name": "军工电子",
        "pct": -0.93,
        "net_yi": -7.59,
        "inflow_yi": 38.78,
        "outflow_yi": 46.37,
        "rank": 68,
        "leader": "邦彦技术",
        "leader_pct": 3.91,
        "company_count": 61.0
      },
      {
        "name": "生物制品",
        "pct": -0.93,
        "net_yi": -8.38,
        "inflow_yi": 27.75,
        "outflow_yi": 36.12,
        "rank": 69,
        "leader": "万泽股份",
        "leader_pct": 3.02,
        "company_count": 55.0
      },
      {
        "name": "汽车零部件",
        "pct": -1.01,
        "net_yi": -34.32,
        "inflow_yi": 157.93,
        "outflow_yi": 192.25,
        "rank": 70,
        "leader": "大地电气",
        "leader_pct": 11.1,
        "company_count": 275.0
      },
      {
        "name": "黑色家电",
        "pct": -1.08,
        "net_yi": -1.37,
        "inflow_yi": 4.52,
        "outflow_yi": 5.89,
        "rank": 71,
        "leader": "四川九洲",
        "leader_pct": 0.24,
        "company_count": 9.0
      },
      {
        "name": "橡胶制品",
        "pct": -1.25,
        "net_yi": -0.96,
        "inflow_yi": 5.36,
        "outflow_yi": 6.32,
        "rank": 72,
        "leader": "三力士",
        "leader_pct": 2.14,
        "company_count": 22.0
      },
      {
        "name": "电池",
        "pct": -1.32,
        "net_yi": -17.69,
        "inflow_yi": 131.54,
        "outflow_yi": 149.22,
        "rank": 73,
        "leader": "华汇智能",
        "leader_pct": 111.75,
        "company_count": 107.0
      },
      {
        "name": "塑料制品",
        "pct": -1.34,
        "net_yi": -7.36,
        "inflow_yi": 54.0,
        "outflow_yi": 61.36,
        "rank": 74,
        "leader": "津膜科技",
        "leader_pct": 5.84,
        "company_count": 77.0
      },
      {
        "name": "通用设备",
        "pct": -1.36,
        "net_yi": -43.71,
        "inflow_yi": 191.36,
        "outflow_yi": 235.07,
        "rank": 75,
        "leader": "*ST宝馨",
        "leader_pct": 9.05,
        "company_count": 253.0
      },
      {
        "name": "工业金属",
        "pct": -1.49,
        "net_yi": -45.23,
        "inflow_yi": 91.55,
        "outflow_yi": 136.77,
        "rank": 76,
        "leader": "豪美新材",
        "leader_pct": 7.39,
        "company_count": 55.0
      },
      {
        "name": "通信设备",
        "pct": -1.64,
        "net_yi": -40.15,
        "inflow_yi": 461.74,
        "outflow_yi": 501.89,
        "rank": 77,
        "leader": "楚天龙",
        "leader_pct": 10.0,
        "company_count": 91.0
      },
      {
        "name": "光学光电子",
        "pct": -1.65,
        "net_yi": -44.64,
        "inflow_yi": 110.62,
        "outflow_yi": 155.26,
        "rank": 78,
        "leader": "久量股份",
        "leader_pct": 6.05,
        "company_count": 107.0
      },
      {
        "name": "金属新材料",
        "pct": -1.68,
        "net_yi": -8.53,
        "inflow_yi": 17.02,
        "outflow_yi": 25.55,
        "rank": 79,
        "leader": "昆工科技",
        "leader_pct": 2.65,
        "company_count": 34.0
      },
      {
        "name": "小金属",
        "pct": -1.7,
        "net_yi": -34.8,
        "inflow_yi": 57.41,
        "outflow_yi": 92.21,
        "rank": 80,
        "leader": "金钛股份",
        "leader_pct": 15.72,
        "company_count": 30.0
      },
      {
        "name": "贵金属",
        "pct": -1.78,
        "net_yi": -7.33,
        "inflow_yi": 92.88,
        "outflow_yi": 100.21,
        "rank": 81,
        "leader": "山东黄金",
        "leader_pct": 1.07,
        "company_count": 14.0
      },
      {
        "name": "自动化设备",
        "pct": -1.84,
        "net_yi": -31.62,
        "inflow_yi": 125.76,
        "outflow_yi": 157.38,
        "rank": 82,
        "leader": "德龙激光",
        "leader_pct": 17.5,
        "company_count": 99.0
      },
      {
        "name": "电机",
        "pct": -2.03,
        "net_yi": -6.02,
        "inflow_yi": 10.86,
        "outflow_yi": 16.88,
        "rank": 83,
        "leader": "神力股份",
        "leader_pct": 1.31,
        "company_count": 26.0
      },
      {
        "name": "其他电子",
        "pct": -2.05,
        "net_yi": -24.0,
        "inflow_yi": 45.83,
        "outflow_yi": 69.83,
        "rank": 84,
        "leader": "伊戈尔",
        "leader_pct": 2.77,
        "company_count": 34.0
      },
      {
        "name": "消费电子",
        "pct": -2.06,
        "net_yi": -37.56,
        "inflow_yi": 160.58,
        "outflow_yi": 198.14,
        "rank": 85,
        "leader": "绿联科技",
        "leader_pct": 5.57,
        "company_count": 96.0
      },
      {
        "name": "非金属材料",
        "pct": -2.12,
        "net_yi": -6.58,
        "inflow_yi": 18.7,
        "outflow_yi": 25.29,
        "rank": 86,
        "leader": "宁新新材",
        "leader_pct": 1.35,
        "company_count": 17.0
      },
      {
        "name": "能源金属",
        "pct": -2.65,
        "net_yi": -16.19,
        "inflow_yi": 23.22,
        "outflow_yi": 39.41,
        "rank": 87,
        "leader": "*ST威领",
        "leader_pct": -0.66,
        "company_count": 13.0
      },
      {
        "name": "元件",
        "pct": -2.73,
        "net_yi": -43.6,
        "inflow_yi": 303.25,
        "outflow_yi": 346.85,
        "rank": 88,
        "leader": "景旺电子",
        "leader_pct": 8.96,
        "company_count": 63.0
      },
      {
        "name": "半导体",
        "pct": -2.82,
        "net_yi": -158.72,
        "inflow_yi": 740.32,
        "outflow_yi": 899.04,
        "rank": 89,
        "leader": "灿瑞科技",
        "leader_pct": 11.02,
        "company_count": 187.0
      },
      {
        "name": "电子化学品",
        "pct": -3.39,
        "net_yi": -22.4,
        "inflow_yi": 103.95,
        "outflow_yi": 126.36,
        "rank": 90,
        "leader": "方邦股份",
        "leader_pct": 4.05,
        "company_count": 43.0
      }
    ],
    "concept": [],
    "target_sectors": [
      {
        "sector": "新材料/玻纤",
        "match_industry": "金属新材料",
        "industry_net_yi": -8.53,
        "match_concept": null,
        "concept_net_yi": null
      },
      {
        "sector": "半导体/存储",
        "match_industry": "半导体",
        "industry_net_yi": -158.72,
        "match_concept": null,
        "concept_net_yi": null
      }
    ],
    "top_inflow": [
      {
        "name": "军工装备",
        "net_yi": 41.69,
        "pct": 0.94
      },
      {
        "name": "白酒",
        "net_yi": 31.74,
        "pct": 2.87
      },
      {
        "name": "文化传媒",
        "net_yi": 28.93,
        "pct": 2.44
      },
      {
        "name": "软件开发",
        "net_yi": 25.63,
        "pct": 1.31
      },
      {
        "name": "游戏",
        "net_yi": 24.52,
        "pct": 1.81
      }
    ],
    "top_outflow": [
      {
        "name": "半导体",
        "net_yi": -158.72,
        "pct": -2.82
      },
      {
        "name": "工业金属",
        "net_yi": -45.23,
        "pct": -1.49
      },
      {
        "name": "光学光电子",
        "net_yi": -44.64,
        "pct": -1.65
      },
      {
        "name": "通用设备",
        "net_yi": -43.71,
        "pct": -1.36
      },
      {
        "name": "元件",
        "net_yi": -43.6,
        "pct": -2.73
      }
    ],
    "error": "概念资金流异常: Length mismatch: Expected axis has 12 elements, new values have 11 elements"
  },
  "event_calendar": {
    "as_of": "2026-09-07",
    "events": [
      {
        "ticker": null,
        "name": "宏观事件",
        "event_type": "macro",
        "event_date": "2026-09-15",
        "detail": "FOMC利率决议+SEP经济预测(9/15-16)",
        "status": "upcoming",
        "impact": "HIGH",
        "note": "⚠️ 沃什杰克逊霍尔暗示加息。9月加息概率60%。距今13天。US30Y已破5.0%"
      }
    ],
    "count": 1
  },
  "sector_heat": {
    "ok": true,
    "board": [
      {
        "name": "船舶制造",
        "pct": 5.9116,
        "amount": 14086436945.0,
        "count": 8.0,
        "top_stock_pct": 9.178
      },
      {
        "name": "农林牧渔",
        "pct": 3.3727,
        "amount": 11948533042.0,
        "count": 64.0,
        "top_stock_pct": 10.101
      },
      {
        "name": "酿酒行业",
        "pct": 2.6337,
        "amount": 11015944122.0,
        "count": 33.0,
        "top_stock_pct": 10.06
      },
      {
        "name": "水泥行业",
        "pct": 1.5267,
        "amount": 2458673552.0,
        "count": 26.0,
        "top_stock_pct": 9.916
      },
      {
        "name": "商业百货",
        "pct": 1.3941,
        "amount": 10679050827.0,
        "count": 93.0,
        "top_stock_pct": 10.039
      },
      {
        "name": "印刷包装",
        "pct": 1.3758,
        "amount": 251031367.0,
        "count": 20.0,
        "top_stock_pct": 2.769
      },
      {
        "name": "服装鞋类",
        "pct": 1.2774,
        "amount": 3592052520.0,
        "count": 49.0,
        "top_stock_pct": 7.659
      },
      {
        "name": "家具行业",
        "pct": 1.229,
        "amount": 342313807.0,
        "count": 16.0,
        "top_stock_pct": 4.46
      },
      {
        "name": "传媒娱乐",
        "pct": 1.1441,
        "amount": 3723886233.0,
        "count": 40.0,
        "top_stock_pct": 6.241
      },
      {
        "name": "飞机制造",
        "pct": 1.1294,
        "amount": 6044356550.0,
        "count": 14.0,
        "top_stock_pct": 4.148
      }
    ],
    "target_sectors": [],
    "error": null
  },
  "data_quality": {
    "timestamp": "2026-09-07T09:02:10.896168",
    "sources": [
      "akshare",
      "data_layer",
      "eastmoney_fund_flow",
      "sina"
    ],
    "cautions": [
      "行业资金流采集失败: 个股资金流采集异常: Length mismatch: Expected axis has 13 elements, new values have 10 elements"
    ],
    "completeness": 1.0
  },
  "_notes": {
    "holdings": "持仓股诊断：OHLCV + MA5/10/20/60 + LR + 止损判定 + 趋势分析",
    "index_snapshot": "A股三大指数实时快照（新浪API）",
    "macro_context": "宏观环境：美债/美元/A50/美股/SOX（部分可能因API限制降级）",
    "individual_fund_flow": "持仓股个股资金流：流入/流出/净额(亿) + 换手率 (东方财富, ~30s延迟)",
    "sector_fund_flow": "板块资金流：90个行业 + 386个概念板块的流入/流出/净额 + 持仓关联板块匹配",
    "event_calendar": "未来15天分红/解禁/股东大会（优先读 event_calendar.json）",
    "sector_heat": "持仓股所属板块在新浪49行业中的涨跌幅排名",
    "data_quality": "数据质量自检：完整度 + 交叉验证 + CAUTION标注",
    "ai_next_steps": [
      "读取 morning_data.json 的 individual_fund_flow + sector_fund_flow 执行跨维度叙事合成",
      "读取 macro_event_monitor.py 的 macro_report_latest.json 补充5层审计",
      "AI 通过 WebSearch 补充 macro_shock_audit（Fed/亚太/美股隔夜/shock评级）",
      "AI 合成情绪评分（涨停/跌停家数 + 融资余额 + 北向情绪）",
      "AI 执行逆向审计 + 红蓝对抗（提示词2）",
      "读取 offensive_signal.json 解读进攻信号（提示词2.5）",
      "执行4层收敛法：技术信号+资金流+情绪+宏观shock → verdict"
    ]
  }
}