#!/usr/bin/env python3
"""
调试视频标签问题
Debug Video Tagging Issues
"""

import logging
import numpy as np
from models import DatabaseSession
from database import get_frame_times_features_by_path, get_video_paths
from auto_tag import AutoTagger

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_video_features():
    """测试视频特征处理"""
    print("🔍 调试视频标签问题")
    print("="*50)
    
    # 创建自动标签器
    tagger = AutoTagger()
    
    # 获取第一个视频进行测试
    with DatabaseSession() as session:
        video_paths = list(get_video_paths(session))
    
    if not video_paths:
        print("❌ 没有找到视频")
        return
    
    test_video = video_paths[0]
    print(f"测试视频: {test_video}")
    
    # 获取视频特征
    with DatabaseSession() as session:
        frame_times, features = get_frame_times_features_by_path(session, test_video)
    
    print(f"找到 {len(features)} 个帧")
    
    if not features:
        print("❌ 没有找到视频特征")
        return
    
    # 测试第一个帧的特征
    first_feature = features[0]
    print(f"第一个帧特征大小: {len(first_feature)} 字节")
    
    # 转换为numpy数组
    try:
        feature_array = np.frombuffer(first_feature, dtype=np.float32)
        print(f"特征数组形状: {feature_array.shape}")
        print(f"特征数组类型: {feature_array.dtype}")
        print(f"特征数组范围: {feature_array.min():.4f} 到 {feature_array.max():.4f}")
        
        # 重塑为2D数组
        feature_array = feature_array.reshape(1, -1)
        print(f"重塑后形状: {feature_array.shape}")
        
        # 计算相似度
        similarities = tagger.compute_similarity(feature_array, tagger.tag_vectors)
        print(f"相似度数组形状: {similarities.shape}")
        print(f"相似度范围: {similarities.min():.4f} 到 {similarities.max():.4f}")
        
        # 获取标签
        top_tags = tagger.get_top_tags(similarities, top_k=5, threshold=0.3)
        print(f"前5个标签: {top_tags}")
        
        if top_tags:
            print("✅ 标签生成成功！")
        else:
            print("❌ 没有找到匹配的标签")
            
    except Exception as e:
        print(f"❌ 处理特征时出错: {e}")
        import traceback
        traceback.print_exc()

def test_tag_vectors():
    """测试标签向量"""
    print("\n🔍 测试标签向量")
    print("="*30)
    
    tagger = AutoTagger()
    
    print(f"标签向量形状: {tagger.tag_vectors.shape}")
    print(f"标签向量类型: {tagger.tag_vectors.dtype}")
    print(f"标签向量范围: {tagger.tag_vectors.min():.4f} 到 {tagger.tag_vectors.max():.4f}")
    
    # 显示前几个标签
    from tag_vocabulary import ENGLISH_TAGS
    print(f"前10个英文标签: {ENGLISH_TAGS[:10]}")

def test_similarity_threshold():
    """测试相似度阈值"""
    print("\n🔍 测试相似度阈值")
    print("="*30)
    
    tagger = AutoTagger()
    
    # 创建一个测试特征（全零）
    test_feature = np.zeros((1, tagger.tag_vectors.shape[1]), dtype=np.float32)
    
    # 计算相似度
    similarities = tagger.compute_similarity(test_feature, tagger.tag_vectors)
    
    print(f"测试特征相似度范围: {similarities.min():.4f} 到 {similarities.max():.4f}")
    
    # 测试不同阈值
    for threshold in [0.1, 0.2, 0.3, 0.4, 0.5]:
        top_tags = tagger.get_top_tags(similarities, top_k=5, threshold=threshold)
        print(f"阈值 {threshold}: {len(top_tags)} 个标签")

if __name__ == "__main__":
    test_tag_vectors()
    test_similarity_threshold()
    test_video_features() 