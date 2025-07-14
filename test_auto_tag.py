#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自动标签脚本
"""

import logging
import sys

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """测试导入是否正常"""
    try:
        logger.info("测试导入模块...")
        
        # 测试基础模块导入
        import numpy as np
        import torch
        logger.info("✓ numpy 和 torch 导入成功")
        
        # 测试项目模块导入
        from config import *
        logger.info("✓ config 导入成功")
        
        from models import DatabaseSession, Image, Video
        logger.info("✓ models 导入成功")
        
        from process_assets import process_text
        logger.info("✓ process_assets 导入成功")
        
        from tag_vocabulary import ENGLISH_TAGS, ENGLISH_TO_CHINESE
        logger.info("✓ tag_vocabulary 导入成功")
        
        from auto_tag import AutoTagger
        logger.info("✓ AutoTagger 导入成功")
        
        return True
        
    except Exception as e:
        logger.error(f"导入失败: {e}")
        return False

def test_tag_vectors():
    """测试标签向量计算"""
    try:
        logger.info("测试标签向量计算...")
        
        from auto_tag import AutoTagger
        
        # 创建自动标签器
        tagger = AutoTagger(tag_cache_file="test_tag_vectors.pkl")
        
        # 检查标签向量是否计算成功
        if len(tagger.tag_vectors) > 0:
            logger.info(f"✓ 标签向量计算成功，共 {len(tagger.tag_vectors)} 个标签")
            
            # 测试几个标签
            test_tags = ["beach", "sunset", "person"]
            for tag in test_tags:
                if tag in tagger.tag_vectors:
                    logger.info(f"✓ 标签 '{tag}' 向量计算成功")
                else:
                    logger.warning(f"✗ 标签 '{tag}' 向量计算失败")
            
            return True
        else:
            logger.error("✗ 标签向量计算失败")
            return False
            
    except Exception as e:
        logger.error(f"标签向量测试失败: {e}")
        return False

def test_similarity_computation():
    """测试相似度计算"""
    try:
        logger.info("测试相似度计算...")
        
        from auto_tag import AutoTagger
        import numpy as np
        
        # 创建自动标签器
        tagger = AutoTagger(tag_cache_file="test_tag_vectors.pkl")
        
        # 创建一个测试图片特征向量
        test_feature = np.random.rand(1, 512)  # 假设特征维度为512
        
        # 计算相似度
        similarities = tagger.compute_similarity(test_feature, tagger.tag_vectors)
        
        if similarities:
            logger.info(f"✓ 相似度计算成功，共 {len(similarities)} 个标签")
            
            # 获取top标签
            top_tags = tagger.get_top_tags(similarities, top_k=3, threshold=0.0)
            logger.info(f"✓ Top标签获取成功: {top_tags}")
            
            return True
        else:
            logger.error("✗ 相似度计算失败")
            return False
            
    except Exception as e:
        logger.error(f"相似度计算测试失败: {e}")
        return False

def main():
    """主测试函数"""
    logger.info("开始测试自动标签功能...")
    
    # 测试导入
    if not test_imports():
        logger.error("导入测试失败，退出")
        sys.exit(1)
    
    # 测试标签向量计算
    if not test_tag_vectors():
        logger.error("标签向量测试失败，退出")
        sys.exit(1)
    
    # 测试相似度计算
    if not test_similarity_computation():
        logger.error("相似度计算测试失败，退出")
        sys.exit(1)
    
    logger.info("所有测试通过！自动标签功能正常工作。")

if __name__ == "__main__":
    main() 