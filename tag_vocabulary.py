# 候选标签库 - 中英文对照
# 格式: {"中文标签": "英文标签", ...}
# 这些标签将被用于自动识别图片和视频内容

TAG_VOCABULARY = {
    # 自然景观
    "海滩": "beach",
    "海洋": "ocean",
    "海浪": "waves",
    "沙滩": "sand",
    "日落": "sunset",
    "日出": "sunrise",
    "天空": "sky",
    "云朵": "clouds",
    "山脉": "mountains",
    "森林": "forest",
    "树木": "trees",
    "草地": "grass",
    "花朵": "flowers",
    "瀑布": "waterfall",
    "河流": "river",
    "湖泊": "lake",
    "雪景": "snow",
    "雨景": "rain",
    
    # 城市景观
    "城市": "city",
    "建筑": "building",
    "高楼": "skyscraper",
    "街道": "street",
    "道路": "road",
    "桥梁": "bridge",
    "公园": "park",
    "广场": "square",
    "夜景": "night scene",
    "灯光": "lights",
    
    # 人物
    "人": "person",
    "男人": "man",
    "女人": "woman",
    "孩子": "child",
    "老人": "elderly",
    "年轻人": "young person",
    "微笑": "smile",
    "表情": "expression",
    "动作": "action",
    "运动": "sports",
    "舞蹈": "dance",
    
    # 动物
    "动物": "animal",
    "狗": "dog",
    "猫": "cat",
    "鸟": "bird",
    "鱼": "fish",
    "马": "horse",
    "牛": "cow",
    "羊": "sheep",
    "鸡": "chicken",
    "蝴蝶": "butterfly",
    
    # 交通工具
    "汽车": "car",
    "自行车": "bicycle",
    "摩托车": "motorcycle",
    "公交车": "bus",
    "火车": "train",
    "飞机": "airplane",
    "船": "ship",
    "飞机": "aircraft",
    
    # 食物
    "食物": "food",
    "水果": "fruit",
    "蔬菜": "vegetables",
    "面包": "bread",
    "蛋糕": "cake",
    "咖啡": "coffee",
    "茶": "tea",
    "饮料": "drink",
    
    # 颜色
    "红色": "red",
    "蓝色": "blue",
    "绿色": "green",
    "黄色": "yellow",
    "橙色": "orange",
    "紫色": "purple",
    "粉色": "pink",
    "白色": "white",
    "黑色": "black",
    "灰色": "gray",
    
    # 时间
    "白天": "daytime",
    "夜晚": "night",
    "黄昏": "dusk",
    "黎明": "dawn",
    "早晨": "morning",
    "下午": "afternoon",
    "傍晚": "evening",
    
    # 天气
    "晴天": "sunny",
    "阴天": "cloudy",
    "雨天": "rainy",
    "雪天": "snowy",
    "雾天": "foggy",
    "风": "wind",
    
    # 活动
    "工作": "work",
    "学习": "study",
    "游戏": "game",
    "音乐": "music",
    "电影": "movie",
    "阅读": "reading",
    "烹饪": "cooking",
    "清洁": "cleaning",
    "购物": "shopping",
    "旅行": "travel",
    
    # 情感
    "快乐": "happy",
    "悲伤": "sad",
    "愤怒": "angry",
    "平静": "calm",
    "兴奋": "excited",
    "放松": "relaxed",
    "紧张": "nervous",
    
    # 技术
    "电脑": "computer",
    "手机": "phone",
    "相机": "camera",
    "电视": "television",
    "屏幕": "screen",
    "键盘": "keyboard",
    "鼠标": "mouse",
    
    # 抽象概念
    "美丽": "beautiful",
    "优雅": "elegant",
    "现代": "modern",
    "传统": "traditional",
    "简单": "simple",
    "复杂": "complex",
    "明亮": "bright",
    "黑暗": "dark",
    "温暖": "warm",
    "寒冷": "cold",
    "安静": "quiet",
    "喧闹": "noisy",
}

# 获取所有英文标签列表
ENGLISH_TAGS = list(TAG_VOCABULARY.values())

# 获取中文到英文的映射
CHINESE_TO_ENGLISH = TAG_VOCABULARY

# 获取英文到中文的映射
ENGLISH_TO_CHINESE = {v: k for k, v in TAG_VOCABULARY.items()} 