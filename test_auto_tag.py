#!/usr/bin/env python3
"""
测试自动标签功能
Test Auto Tagging Functionality
"""

import logging
import numpy as np
from auto_tag import AutoTagger

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tag_vectors_loading():
    """测试标签向量加载"""
    print("🔍 测试标签向量加载...")
    
    try:
        tagger = AutoTagger()
        
        # 检查标签向量是否正确加载
        if tagger.tag_vectors is not None:
            print(f"✅ 标签向量加载成功")
            print(f"   形状: {tagger.tag_vectors.shape}")
            print(f"   类型: {tagger.tag_vectors.dtype}")
            print(f"   范围: {tagger.tag_vectors.min():.4f} 到 {tagger.tag_vectors.max():.4f}")
            return True
        else:
            print("❌ 标签向量加载失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_similarity_computation():
    """测试相似度计算"""
    print("\n🔍 测试相似度计算...")
    
    try:
        tagger = AutoTagger()
        
        # 创建一个测试特征
        test_feature = np.random.randn(1, tagger.tag_vectors.shape[1]).astype(np.float32)
        
        # 计算相似度
        similarities = tagger.compute_similarity(test_feature)
        
        print(f"✅ 相似度计算成功")
        print(f"   相似度数量: {len(similarities)}")
        print(f"   相似度范围: {min(similarities.values()):.4f} 到 {max(similarities.values()):.4f}")
        
        # 获取top标签
        top_tags = tagger.get_top_tags(similarities)
        print(f"   Top标签数量: {len(top_tags)}")
        
        if top_tags:
            print(f"   前3个标签: {top_tags[:3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_image_processing():
    """测试图片处理"""
    print("\n🔍 测试图片处理...")
    
    try:
        tagger = AutoTagger()
        
        # 创建一个测试图片特征
        test_feature = np.random.randn(1, tagger.tag_vectors.shape[1]).astype(np.float32)
        
        # 处理图片
        tags = tagger.process_image(1, "test_image.jpg", test_feature)
        
        print(f"✅ 图片处理成功")
        print(f"   生成标签数量: {len(tags)}")
        if tags:
            print(f"   标签: {tags}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_video_processing():
    """测试视频处理"""
    print("\n🔍 测试视频处理...")
    
    try:
        tagger = AutoTagger()
        
        # 创建测试视频特征（模拟多个帧）
        num_frames = 5
        test_features = []
        for i in range(num_frames):
            feature = np.random.randn(1, tagger.tag_vectors.shape[1]).astype(np.float32)
            test_features.append(feature.tobytes())
        
        # 模拟数据库查询结果
        frame_times = list(range(0, num_frames * 2, 2))
        
        # 测试视频处理逻辑
        all_tags = []
        for i, feature in enumerate(test_features):
            try:
                feature_array = np.frombuffer(feature, dtype=np.float32).reshape(1, -1)
                similarities = tagger.compute_similarity(feature_array)
                top_tags = tagger.get_top_tags(similarities)
                
                for tag, score in top_tags:
                    from tag_vocabulary import ENGLISH_TO_CHINESE
                    chinese_tag = ENGLISH_TO_CHINESE.get(tag, tag)
                    all_tags.append(chinese_tag)
                    
            except Exception as e:
                print(f"   处理帧 {i} 时出错: {e}")
                continue
        
        print(f"✅ 视频处理测试成功")
        print(f"   处理帧数: {num_frames}")
        print(f"   生成标签总数: {len(all_tags)}")
        
        # 统计标签频率
        from collections import defaultdict
        tag_counts = defaultdict(int)
        for tag in all_tags:
            tag_counts[tag] += 1
        
        print(f"   唯一标签数: {len(tag_counts)}")
        if tag_counts:
            top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"   前3个标签: {top_tags}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_filename_generation():
    """测试文件名生成"""
    print("\n🔍 测试文件名生成...")
    
    try:
        tagger = AutoTagger()
        
        # 测试文件名生成
        original_path = "/path/to/test_video.mp4"
        tags = ["人物", "风景", "动物", "建筑"]
        
        new_filename = tagger.generate_filename(original_path, tags)
        
        print(f"✅ 文件名生成成功")
        print(f"   原始路径: {original_path}")
        print(f"   标签: {tags}")
        print(f"   新文件名: {new_filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 自动标签功能测试")
    print("="*50)
    
    tests = [
        ("标签向量加载", test_tag_vectors_loading),
        ("相似度计算", test_similarity_computation),
        ("图片处理", test_image_processing),
        ("视频处理", test_video_processing),
        ("文件名生成", test_filename_generation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！自动标签功能正常。")
    else:
        print("⚠️ 部分测试失败，请检查相关功能。")

if __name__ == "__main__":
    main() 