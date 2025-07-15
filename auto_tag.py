#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动标签脚本
利用MaterialSearch的向量数据库和CLIP模型，为图片和视频自动添加标签
"""

import json
import logging
import os
import pickle
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import numpy as np
from tqdm import tqdm

from config import *
from database import get_image_id_path_features, get_video_paths, get_frame_times_features_by_path
from models import DatabaseSession, Image, Video
from process_assets import process_text
from tag_vocabulary import ENGLISH_TAGS, ENGLISH_TO_CHINESE

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AutoTagger:
    """自动标签器类"""
    
    def __init__(self, tag_cache_file: str = "tag_vectors.pkl", 
                 similarity_threshold: float = 0.3,
                 top_k: int = 5,
                 video_min_frequency: int = 2):
        """
        初始化自动标签器
        
        Args:
            tag_cache_file: 标签向量缓存文件路径
            similarity_threshold: 相似度阈值
            top_k: 返回前k个标签
            video_min_frequency: 视频标签最小出现频率
        """
        self.tag_cache_file = tag_cache_file
        self.similarity_threshold = similarity_threshold
        self.top_k = top_k
        self.video_min_frequency = video_min_frequency
        self.tag_vectors: Optional[np.ndarray] = None
        self._load_or_compute_tag_vectors()
    
    def _load_or_compute_tag_vectors(self) -> None:
        """加载或计算标签向量"""
        if os.path.exists(self.tag_cache_file):
            logger.info(f"从缓存文件加载标签向量: {self.tag_cache_file}")
            try:
                with open(self.tag_cache_file, 'rb') as f:
                    loaded_data = pickle.load(f)
                
                # 处理不同格式的缓存数据
                if isinstance(loaded_data, dict):
                    # 旧格式：字典格式
                    self.tag_vectors = np.stack([v for v in loaded_data.values()])
                elif isinstance(loaded_data, np.ndarray):
                    # 新格式：numpy数组
                    self.tag_vectors = loaded_data
                else:
                    raise ValueError(f"未知的缓存格式: {type(loaded_data)}")
                
                logger.info(f"成功加载 {self.tag_vectors.shape[0]} 个标签向量")
                return
                
            except Exception as e:
                logger.warning(f"加载标签向量缓存失败: {e}")
        
        logger.info("开始计算标签向量...")
        self._compute_tag_vectors()
        self._save_tag_vectors()
    
    def _compute_tag_vectors(self) -> None:
        """计算所有标签的向量"""
        logger.info(f"正在为 {len(ENGLISH_TAGS)} 个标签计算向量...")
        
        vectors = []
        valid_tags = []
        
        for tag in tqdm(ENGLISH_TAGS, desc="计算标签向量"):
            text_feature = process_text(tag)
            if text_feature is None:
                logger.warning(f"无法计算标签向量: {tag}")
                continue
            
            vectors.append(text_feature.flatten())
            valid_tags.append(tag)
        
        if not vectors:
            raise RuntimeError("没有成功计算任何标签向量")
        
        self.tag_vectors = np.stack(vectors)
        logger.info(f"完成标签向量计算，共 {self.tag_vectors.shape[0]} 个标签")
    
    def _save_tag_vectors(self) -> None:
        """保存标签向量到缓存文件"""
        try:
            with open(self.tag_cache_file, 'wb') as f:
                pickle.dump(self.tag_vectors, f)
            logger.info(f"标签向量已保存到: {self.tag_cache_file}")
        except Exception as e:
            logger.error(f"保存标签向量失败: {e}")
    
    def compute_similarity(self, image_feature: np.ndarray) -> Dict[str, float]:
        """
        计算图片特征与标签向量的相似度
        
        Args:
            image_feature: 图片特征向量
            
        Returns:
            相似度分数字典
        """
        if self.tag_vectors is None:
            raise RuntimeError("标签向量未初始化")
        
        image_feature = image_feature.flatten()
        
        # 计算余弦相似度
        # 添加小量避免除零
        norm_product = (np.linalg.norm(self.tag_vectors, axis=1) * 
                       np.linalg.norm(image_feature) + 1e-8)
        similarities = np.dot(self.tag_vectors, image_feature) / norm_product
        
        return {ENGLISH_TAGS[i]: float(sim) for i, sim in enumerate(similarities)}
    
    def get_top_tags(self, similarities: Dict[str, float]) -> List[Tuple[str, float]]:
        """
        获取相似度最高的标签
        
        Args:
            similarities: 相似度字典
            
        Returns:
            标签和分数的元组列表
        """
        # 过滤低于阈值的标签
        filtered_similarities = {
            tag: score for tag, score in similarities.items() 
            if score >= self.similarity_threshold
        }
        
        # 按相似度排序
        sorted_tags = sorted(filtered_similarities.items(), 
                           key=lambda x: x[1], reverse=True)
        
        # 返回前k个标签
        return sorted_tags[:self.top_k]
    
    def process_image(self, image_id: int, image_path: str, 
                     image_feature: np.ndarray) -> List[str]:
        """
        处理单张图片
        
        Args:
            image_id: 图片ID
            image_path: 图片路径
            image_feature: 图片特征
            
        Returns:
            中文标签列表
        """
        try:
            # 计算相似度
            similarities = self.compute_similarity(image_feature)
            
            # 获取top标签
            top_tags = self.get_top_tags(similarities)
            
            if not top_tags:
                logger.warning(f"图片 {image_path} 没有找到匹配的标签")
                return []
            
            # 转换为中文标签
            chinese_tags = []
            for tag, score in top_tags:
                chinese_tag = ENGLISH_TO_CHINESE.get(tag, tag)
                chinese_tags.append(chinese_tag)
                logger.debug(f"图片 {image_path}: {chinese_tag} (相似度: {score:.3f})")
            
            return chinese_tags
            
        except Exception as e:
            logger.error(f"处理图片 {image_path} 时出错: {e}")
            return []
    
    def process_video(self, video_path: str) -> List[str]:
        """
        处理视频，分析所有帧并合并标签
        
        Args:
            video_path: 视频路径
            
        Returns:
            视频标签列表
        """
        logger.info(f"处理视频: {video_path}")
        
        try:
            with DatabaseSession() as session:
                frame_times, features = get_frame_times_features_by_path(session, video_path)
            
            if not features:
                logger.warning(f"视频 {video_path} 没有找到帧特征")
                return []
            
            # 处理所有帧
            all_tags = []
            for i, feature in enumerate(features):
                try:
                    feature_array = np.frombuffer(feature, dtype=np.float32).reshape(1, -1)
                    similarities = self.compute_similarity(feature_array)
                    top_tags = self.get_top_tags(similarities)
                    
                    for tag, score in top_tags:
                        chinese_tag = ENGLISH_TO_CHINESE.get(tag, tag)
                        all_tags.append(chinese_tag)
                        
                except Exception as e:
                    logger.warning(f"处理视频帧 {i} 时出错: {e}")
                    continue
            
            if not all_tags:
                logger.warning(f"视频 {video_path} 没有找到任何标签")
                return []
            
            # 统计标签频率
            tag_counts = defaultdict(int)
            for tag in all_tags:
                tag_counts[tag] += 1
            
            # 按频率排序，取前10个，至少出现指定次数
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
            video_tags = [
                tag for tag, count in sorted_tags[:10] 
                if count >= self.video_min_frequency
            ]
            
            logger.info(f"视频 {video_path} 标签: {video_tags}")
            return video_tags
            
        except Exception as e:
            logger.error(f"处理视频 {video_path} 时出错: {e}")
            return []
    
    def update_database_tags(self, file_type: str, file_id: int, 
                           file_path: str, tags: List[str]) -> bool:
        """
        更新数据库中的标签
        
        Args:
            file_type: 文件类型 ('image' 或 'video')
            file_id: 文件ID
            file_path: 文件路径
            tags: 标签列表
            
        Returns:
            是否更新成功
        """
        try:
            with DatabaseSession() as session:
                if file_type == 'image':
                    record = session.query(Image).filter_by(id=file_id).first()
                else:
                    record = session.query(Video).filter_by(id=file_id).first()
                
                if record is not None:
                    record.tags = json.dumps(tags, ensure_ascii=False)
                    session.commit()
                    logger.info(f"已更新 {file_type} {file_path} 的标签: {tags}")
                    return True
                else:
                    logger.warning(f"未找到 {file_type} 记录: {file_path}")
                    return False
                    
        except Exception as e:
            logger.error(f"更新数据库标签失败: {e}")
            return False
    
    def generate_filename(self, original_path: str, tags: List[str]) -> str:
        """
        根据标签生成新文件名
        
        Args:
            original_path: 原始文件路径
            tags: 标签列表
            
        Returns:
            新文件路径
        """
        if not tags:
            return original_path
        
        # 获取文件信息
        path_obj = Path(original_path)
        extension = path_obj.suffix
        parent_dir = path_obj.parent
        
        # 取前3个标签作为文件名
        tag_part = "_".join(tags[:3])
        
        # 清理标签字符串，移除特殊字符
        tag_part = re.sub(r'[^\w\s-]', '', tag_part)
        tag_part = re.sub(r'[-\s]+', '_', tag_part)
        
        # 生成新文件名
        new_filename = f"{tag_part}{extension}"
        new_path = parent_dir / new_filename
        
        # 如果文件已存在，添加数字后缀
        counter = 1
        while new_path.exists():
            new_filename = f"{tag_part}_{counter}{extension}"
            new_path = parent_dir / new_filename
            counter += 1
        
        return str(new_path)
    
    def rename_file(self, old_path: str, new_path: str) -> bool:
        """
        重命名文件
        
        Args:
            old_path: 旧路径
            new_path: 新路径
            
        Returns:
            是否成功
        """
        try:
            shutil.move(old_path, new_path)
            logger.info(f"文件重命名: {old_path} -> {new_path}")
            return True
        except Exception as e:
            logger.error(f"文件重命名失败: {old_path} -> {new_path}, 错误: {e}")
            return False
    
    def _has_existing_tags(self, file_type: str, file_id: Optional[int] = None, 
                          file_path: Optional[str] = None) -> bool:
        """
        检查文件是否已有标签
        
        Args:
            file_type: 文件类型
            file_id: 文件ID（图片用）
            file_path: 文件路径（视频用）
            
        Returns:
            是否已有标签
        """
        try:
            with DatabaseSession() as session:
                if file_type == 'image':
                    record = session.query(Image).filter_by(id=file_id).first()
                else:
                    record = session.query(Video).filter_by(path=file_path).first()
                
                return record is not None and record.tags is not None
                
        except Exception as e:
            logger.error(f"检查标签状态失败: {e}")
            return False
    
    def process_all_images(self, enable_rename: bool = False) -> None:
        """
        处理所有图片
        
        Args:
            enable_rename: 是否启用重命名
        """
        logger.info("开始处理所有图片...")
        
        try:
            with DatabaseSession() as session:
                ids, paths, features = get_image_id_path_features(session)
            
            if not ids:
                logger.info("数据库中没有图片")
                return
            
            logger.info(f"找到 {len(ids)} 张图片")
            
            processed_count = 0
            for i, (image_id, image_path, image_feature) in enumerate(
                zip(ids, paths, features), 1
            ):
                logger.info(f"处理图片 {i}/{len(ids)}: {image_path}")
                
                # 检查是否已有标签
                if self._has_existing_tags('image', file_id=image_id):
                    logger.info(f"图片 {image_path} 已有标签，跳过")
                    continue
                
                # 处理图片
                feature_array = np.frombuffer(image_feature, dtype=np.float32).reshape(1, -1)
                tags = self.process_image(image_id, image_path, feature_array)
                
                if tags:
                    # 更新数据库
                    if self.update_database_tags('image', image_id, image_path, tags):
                        processed_count += 1
                    
                    # 重命名文件
                    if enable_rename:
                        new_path = self.generate_filename(image_path, tags)
                        if new_path != image_path:
                            if self.rename_file(image_path, new_path):
                                # 更新数据库中的路径
                                with DatabaseSession() as session:
                                    record = session.query(Image).filter_by(id=image_id).first()
                                    if record is not None:
                                        record.path = new_path
                                        session.commit()
            
            logger.info(f"图片处理完成，共处理 {processed_count} 张图片")
            
        except Exception as e:
            logger.error(f"处理图片时出错: {e}")
    
    def process_all_videos(self, enable_rename: bool = False) -> None:
        """
        处理所有视频
        
        Args:
            enable_rename: 是否启用重命名
        """
        logger.info("开始处理所有视频...")
        
        try:
            with DatabaseSession() as session:
                video_paths = list(get_video_paths(session))
            
            if not video_paths:
                logger.info("数据库中没有视频")
                return
            
            logger.info(f"找到 {len(video_paths)} 个视频")
            
            processed_count = 0
            for i, video_path in enumerate(video_paths, 1):
                logger.info(f"处理视频 {i}/{len(video_paths)}: {video_path}")
                
                # 检查是否已有标签
                if self._has_existing_tags('video', file_path=video_path):
                    logger.info(f"视频 {video_path} 已有标签，跳过")
                    continue
                
                # 处理视频
                tags = self.process_video(video_path)
                
                if tags:
                    # 更新数据库中该视频的所有帧记录
                    try:
                        with DatabaseSession() as session:
                            video_records = session.query(Video).filter_by(path=video_path).all()
                            for record in video_records:
                                record.tags = json.dumps(tags, ensure_ascii=False)
                            session.commit()
                        processed_count += 1
                        
                    except Exception as e:
                        logger.error(f"更新视频标签失败: {e}")
                        continue
                    
                    # 重命名文件
                    if enable_rename:
                        new_path = self.generate_filename(video_path, tags)
                        if new_path != video_path:
                            if self.rename_file(video_path, new_path):
                                # 更新数据库中的所有相关路径
                                try:
                                    with DatabaseSession() as session:
                                        video_records = session.query(Video).filter_by(path=video_path).all()
                                        for record in video_records:
                                            record.path = new_path
                                        session.commit()
                                except Exception as e:
                                    logger.error(f"更新视频路径失败: {e}")
            
            logger.info(f"视频处理完成，共处理 {processed_count} 个视频")
            
        except Exception as e:
            logger.error(f"处理视频时出错: {e}")
    
    def run(self, enable_rename: bool = False) -> None:
        """
        运行自动标签程序
        
        Args:
            enable_rename: 是否启用文件重命名
        """
        logger.info("开始自动标签程序...")
        
        try:
            # 处理图片
            self.process_all_images(enable_rename)
            
            # 处理视频
            self.process_all_videos(enable_rename)
            
            logger.info("自动标签程序完成！")
            
        except Exception as e:
            logger.error(f"自动标签程序执行失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="自动标签脚本")
    parser.add_argument("--rename", action="store_true", help="启用文件重命名")
    parser.add_argument("--images-only", action="store_true", help="只处理图片")
    parser.add_argument("--videos-only", action="store_true", help="只处理视频")
    parser.add_argument("--threshold", type=float, default=0.3, help="相似度阈值")
    parser.add_argument("--top-k", type=int, default=5, help="返回前k个标签")
    parser.add_argument("--min-frequency", type=int, default=2, help="视频标签最小出现频率")
    
    args = parser.parse_args()
    
    try:
        # 创建自动标签器
        tagger = AutoTagger(
            similarity_threshold=args.threshold,
            top_k=args.top_k,
            video_min_frequency=args.min_frequency
        )
        
        if args.images_only:
            tagger.process_all_images(args.rename)
        elif args.videos_only:
            tagger.process_all_videos(args.rename)
        else:
            tagger.run(args.rename)
            
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        raise


if __name__ == "__main__":
    main() 