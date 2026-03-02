#!/usr/bin/env python3
"""
智能ETF下载器 - 基于实际上市时间下载ETF数据
根据ETF上市时间智能设置开始日期，确保数据完整性和避免下载失败
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import tushare as ts
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("etf_download.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


class SmartETFDownloader:
    """智能ETF下载器"""

    def __init__(self, config_file: str = None):
        """
        初始化下载器

        Args:
            config_file: 配置文件路径
        """
        self.base_dir = Path("raw/ETF")
        self.daily_dir = self.base_dir / "daily"

        # 创建目录
        self.base_dir.mkdir(exist_ok=True)
        self.daily_dir.mkdir(exist_ok=True)

        # 加载下载配置
        self.load_download_config(config_file)

        # 初始化Tushare API
        self.init_tushare()

        # 统计信息
        self.download_stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
        }

    def load_download_config(self, config_file: str = None):
        """加载ETF下载时间配置"""
        if config_file is None:
            config_file = Path(__file__).parent / "etf_download_dates.json"

        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        logger.info(f"✅ 加载ETF配置文件: {config_path}")
        logger.info(
            f"📊 配置包含 {self.config['download_statistics']['total_etfs']} 只ETF"
        )

    def init_tushare(self):
        """初始化Tushare API"""
        # 从配置文件获取token
        token = (
            self.config.get("download_config", {}).get("data_source") == "tushare_pro"
        )
        if token:
            # 从主配置文件读取token
            try:
                with open("config/etf_config.yaml", "r", encoding="utf-8") as f:
                    import yaml

                    main_config = yaml.safe_load(f)
                    token = main_config.get("tushare_token")
            except Exception:
                import os

                token = os.environ.get("TUSHARE_TOKEN")

        if not token:
            raise ValueError("未找到Tushare API token")

        self.pro = ts.pro_api(token)
        logger.info("✅ Tushare API初始化成功")

    def get_etf_download_info(self) -> List[Tuple[str, str, str]]:
        """
        获取所有ETF的下载信息

        Returns:
            List[Tuple[ETF代码, 开始日期, ETF名称]]
        """
        etf_info = []

        # 处理2020年数据可用的ETF
        etf_2020 = self.config["etf_start_dates"]["2020年数据可用ETF"]
        start_date = etf_2020["start_date"]
        for etf_code in etf_2020["etfs"]:
            etf_info.append((etf_code, start_date, f"ETF_{etf_code}"))

        # 处理2021年上市的ETF
        etf_2021 = self.config["etf_start_dates"]["2021年上市ETF"]
        for etf_data in etf_2021["etfs"]:
            if isinstance(etf_data, dict):
                etf_code = etf_data["code"]
                start_date = etf_data["start_date"]
                etf_name = etf_data.get("name", f"ETF_{etf_code}")
            else:
                # 兼容旧格式
                etf_code = etf_data
                start_date = etf_2021["start_date"]
                etf_name = f"ETF_{etf_code}"
            etf_info.append((etf_code, start_date, etf_name))

        # 处理2022年上市的ETF
        etf_2022 = self.config["etf_start_dates"]["2022年上市ETF"]
        for etf_data in etf_2022["etfs"]:
            if isinstance(etf_data, dict):
                etf_code = etf_data["code"]
                start_date = etf_data["start_date"]
                etf_name = etf_data.get("name", f"ETF_{etf_code}")
            else:
                etf_code = etf_data
                start_date = etf_2022["start_date"]
                etf_name = f"ETF_{etf_code}"
            etf_info.append((etf_code, start_date, etf_name))

        return etf_info

    def check_existing_file(
        self, etf_code: str, start_date: str, end_date: str
    ) -> bool:
        """检查ETF数据文件是否已存在且完整"""
        filename = f"{etf_code}_daily_{start_date}_{end_date}.parquet"
        filepath = self.daily_dir / filename

        if not filepath.exists():
            return False

        try:
            # 检查文件完整性
            df = pd.read_parquet(filepath)
            if len(df) > 0:
                logger.debug(f"📄 {etf_code} 数据文件已存在，包含 {len(df)} 条记录")
                return True
        except Exception as e:
            logger.warning(f"⚠️  {etf_code} 数据文件损坏: {e}")

        return False

    def download_etf_data(
        self, etf_code: str, start_date: str, end_date: str, etf_name: str = ""
    ) -> bool:
        """
        下载单只ETF数据

        Args:
            etf_code: ETF代码
            start_date: 开始日期
            end_date: 结束日期
            etf_name: ETF名称

        Returns:
            bool: 下载是否成功
        """
        try:
            # 检查文件是否已存在
            if self.check_existing_file(etf_code, start_date, end_date):
                logger.info(f"⏭️  跳过 {etf_code} - 数据文件已存在")
                self.download_stats["skipped"] += 1
                return True

            logger.info(f"📥 下载 {etf_code} ({etf_name}) - {start_date} ~ {end_date}")

            # 下载数据
            df = self.pro.fund_daily(
                ts_code=etf_code, start_date=start_date, end_date=end_date
            )

            if len(df) == 0:
                logger.warning(f"⚠️  {etf_code} 无数据")
                self.download_stats["failed"] += 1
                self.download_stats["errors"].append(f"{etf_code}: 无数据")
                return False

            # 数据预处理
            df = df.sort_values("trade_date").reset_index(drop=True)

            # 保存数据
            filename = f"{etf_code}_daily_{start_date}_{end_date}.parquet"
            filepath = self.daily_dir / filename

            df.to_parquet(filepath, index=False)

            logger.info(
                f"✅ {etf_code} 下载成功: {len(df)} 条记录 ({df['trade_date'].min()} ~ {df['trade_date'].max()})"
            )
            self.download_stats["success"] += 1

            # 添加延迟避免API限制
            time.sleep(0.2)

            return True

        except Exception as e:
            logger.error(f"❌ {etf_code} 下载失败: {e}")
            self.download_stats["failed"] += 1
            self.download_stats["errors"].append(f"{etf_code}: {str(e)}")
            return False

    def download_all_etfs(self) -> Dict:
        """下载所有ETF数据"""
        logger.info("🚀 开始智能ETF数据下载")
        logger.info(
            f"📊 目标: 下载 {self.config['download_statistics']['total_etfs']} 只ETF"
        )

        # 获取ETF下载信息
        etf_download_info = self.get_etf_download_info()
        self.download_stats["total"] = len(etf_download_info)

        end_date = self.config["download_config"]["default_end_date"]

        # 按分组下载
        logger.info("📅 下载分组1: 2020年数据可用的ETF")
        etf_2020_codes = self.config["etf_start_dates"]["2020年数据可用ETF"]["etfs"]
        etf_2020_start = self.config["etf_start_dates"]["2020年数据可用ETF"][
            "start_date"
        ]

        for etf_code in tqdm(etf_2020_codes, desc="2020年ETF"):
            self.download_etf_data(etf_code, etf_2020_start, end_date)

        logger.info("📅 下载分组2: 2021年上市的ETF")
        etf_2021_data = self.config["etf_start_dates"]["2021年上市ETF"]["etfs"]

        for etf_data in tqdm(etf_2021_data, desc="2021年ETF"):
            if isinstance(etf_data, dict):
                etf_code = etf_data["code"]
                start_date = etf_data["start_date"]
                etf_name = etf_data.get("name", f"ETF_{etf_code}")
            else:
                etf_code = etf_data
                start_date = self.config["etf_start_dates"]["2021年上市ETF"][
                    "start_date"
                ]
                etf_name = f"ETF_{etf_code}"

            self.download_etf_data(etf_code, start_date, end_date, etf_name)

        logger.info("📅 下载分组3: 2022年上市的ETF")
        etf_2022_data = self.config["etf_start_dates"]["2022年上市ETF"]["etfs"]

        for etf_data in tqdm(etf_2022_data, desc="2022年ETF"):
            if isinstance(etf_data, dict):
                etf_code = etf_data["code"]
                start_date = etf_data["start_date"]
                etf_name = etf_data.get("name", f"ETF_{etf_code}")
            else:
                etf_code = etf_data
                start_date = self.config["etf_start_dates"]["2022年上市ETF"][
                    "start_date"
                ]
                etf_name = f"ETF_{etf_code}"

            self.download_etf_data(etf_code, start_date, end_date, etf_name)

        # 2023年上市的ETF（道琼斯）
        if "2023年上市ETF" in self.config["etf_start_dates"]:
            logger.info("📅 下载分组4: 2023年上市的ETF")
            etf_2023_data = self.config["etf_start_dates"]["2023年上市ETF"]["etfs"]

            for etf_data in tqdm(etf_2023_data, desc="2023年ETF"):
                if isinstance(etf_data, dict):
                    etf_code = etf_data["code"]
                    start_date = etf_data["start_date"]
                    etf_name = etf_data.get("name", f"ETF_{etf_code}")
                else:
                    etf_code = etf_data
                    start_date = "20230101"
                    etf_name = f"ETF_{etf_code}"

                self.download_etf_data(etf_code, start_date, end_date, etf_name)

        # 全球资产补充ETF（恒生科技、日经225）
        if "全球资产补充ETF" in self.config["etf_start_dates"]:
            logger.info("📅 下载分组5: 全球资产补充ETF")
            global_etf_data = self.config["etf_start_dates"]["全球资产补充ETF"]["etfs"]

            for etf_data in tqdm(global_etf_data, desc="全球资产ETF"):
                if isinstance(etf_data, dict):
                    etf_code = etf_data["code"]
                    start_date = etf_data["start_date"]
                    etf_name = etf_data.get("name", f"ETF_{etf_code}")
                else:
                    etf_code = etf_data
                    start_date = "20200102"
                    etf_name = f"ETF_{etf_code}"

                self.download_etf_data(etf_code, start_date, end_date, etf_name)

        # 生成下载报告
        self.generate_download_report()

        return self.download_stats

    def generate_download_report(self):
        """生成下载报告"""
        stats = self.download_stats
        success_rate = (
            (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
        )

        report = f"""
# ETF数据下载报告

**下载时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**下载策略**: 基于ETF上市时间的智能下载

## 📊 下载统计

- **总ETF数量**: {stats['total']} 只
- **下载成功**: {stats['success']} 只
- **下载失败**: {stats['failed']} 只
- **跳过已存在**: {stats['skipped']} 只
- **成功率**: {success_rate:.1f}%

## 📁 数据文件位置
- **目录**: {self.daily_dir.absolute()}
- **格式**: Parquet (.parquet)
- **命名**: {{ETF代码}}_daily_{{开始日期}}_{{结束日期}}.parquet

## 📅 时间范围
- **2020年ETF**: 2020-01-02 ~ {self.config['download_config']['default_end_date']} (完整数据)
- **2021年ETF**: 各自上市日 ~ {self.config['download_config']['default_end_date']}
- **2022年ETF**: 各自上市日 ~ {self.config['download_config']['default_end_date']}

"""

        if stats["errors"]:
            report += "## ❌ 下载错误\n\n"
            for error in stats["errors"]:
                report += f"- {error}\n"

        # 保存报告
        report_file = self.base_dir / "download_report.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        logger.info(f"📋 下载报告已保存: {report_file}")

        # 输出摘要
        logger.info("🎉 ETF数据下载完成!")
        logger.info(
            f"✅ 成功: {stats['success']} | ❌ 失败: {stats['failed']} | ⏭️  跳过: {stats['skipped']}"
        )
        logger.info(f"📁 数据文件位置: {self.daily_dir.absolute()}")


def main():
    """主函数"""
    try:
        downloader = SmartETFDownloader()
        stats = downloader.download_all_etfs()

        if stats["failed"] == 0:
            logger.info("🎉 所有ETF数据下载完成!")
            return 0
        else:
            logger.warning(f"⚠️  下载完成，但有 {stats['failed']} 只ETF失败")
            return 1

    except Exception as e:
        logger.error(f"💥 下载过程发生错误: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
