#!/usr/bin/env python3
"""
基于 QMT Bridge SDK 的 ETF 日线数据增量更新脚本

使用方法:
    python update_daily_from_qmt_bridge.py --symbols 510300,510500
    python update_daily_from_qmt_bridge.py --config etf_list.json
    python update_daily_from_qmt_bridge.py --all  # 更新所有配置的ETF
"""

import argparse
import asyncio
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd

try:
    from qmt_bridge import QMTClient, QMTClientConfig
except ImportError:
    print("❌ 请先安装 qmt-data-bridge:")
    print("   pip install qmt-data-bridge")
    exit(1)


class ETFDataUpdater:
    """ETF数据增量更新器"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8001,
        data_dir: str = "./raw/ETF/daily",
    ):
        """
        Args:
            host: QMT Bridge 服务器地址
            port: QMT Bridge 服务器端口
            data_dir: 数据存储目录
        """
        self.config = QMTClientConfig(host=host, port=port)
        self.client = QMTClient(self.config)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _parse_timestamp(self, timestamp_ms: int) -> int:
        """
        将Unix毫秒时间戳转换为YYYYMMDD整数

        Args:
            timestamp_ms: Unix毫秒时间戳

        Returns:
            YYYYMMDD格式的整数，如 20251213
        """
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return int(dt.strftime("%Y%m%d"))

    def _get_last_trade_date(self, symbol: str) -> Optional[int]:
        """
        获取本地数据的最后交易日期

        Args:
            symbol: ETF代码（不含后缀）

        Returns:
            最后交易日期（YYYYMMDD），如果文件不存在返回None
        """
        # 搜索匹配的文件
        files = list(self.data_dir.glob(f"{symbol}.*_daily_*.parquet"))
        if not files:
            return None

        # 如果有多个，取最新的一个
        parquet_file = files[0]

        try:
            df = pd.read_parquet(parquet_file)
            if len(df) > 0 and "trade_date" in df.columns:
                return int(df["trade_date"].max())
        except Exception as e:
            print(f"⚠️  读取 {symbol} 历史数据失败: {e}")

        return None

    async def fetch_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        count: int = 100,
    ) -> List[Dict]:
        """
        获取K线数据

        Args:
            code: 完整股票代码（如 "510300.SH"）
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            count: 获取条数（如果不指定日期范围）

        Returns:
            包含K线数据的字典列表
        """
        try:
            result = await self.client.get_kline(
                code=code,
                period="1d",
                start_time=start_date,
                end_time=end_date,
                count=count,
                dividend_type="front",  # 前复权
            )

            bars = result.get("bars", [])

            # 转换为标准格式
            rows = []
            for bar in bars:
                timestamp_ms = bar.get("time")
                if timestamp_ms is None:
                    continue

                trade_date = self._parse_timestamp(timestamp_ms)
                open_p = bar.get("open")
                high_p = bar.get("high")
                low_p = bar.get("low")
                close_p = bar.get("close")
                vol = bar.get("volume")
                amount = bar.get("amount")

                row = {
                    "ts_code": code,
                    "trade_date": trade_date,
                    "pre_close": None,
                    "open": open_p,
                    "high": high_p,
                    "low": low_p,
                    "close": close_p,
                    "change": None,
                    "pct_chg": None,
                    "vol": vol,
                    "amount": amount,
                    "adj_factor": 1.0,
                    "adj_open": open_p,
                    "adj_high": high_p,
                    "adj_low": low_p,
                    "adj_close": close_p,
                }
                rows.append(row)

            return rows

        except Exception as e:
            print(f"❌ {code} 获取数据失败: {e}")
            return []

    async def update_symbol(
        self, symbol: str, exchange: str = "SH", force_days: Optional[int] = None
    ) -> bool:
        """
        增量更新单个ETF数据

        Args:
            symbol: ETF代码（不含后缀）
            exchange: 交易所代码 (SH/SZ)
            force_days: 强制获取最近N天（用于全量更新）

        Returns:
            是否更新成功
        """
        code = f"{symbol}.{exchange}"

        # 查找现有文件
        files = list(self.data_dir.glob(f"{code}_daily_*.parquet"))
        if files:
            parquet_file = files[0]
        else:
            # 新文件命名规则
            parquet_file = (
                self.data_dir
                / f"{code}_daily_20200101_{datetime.now().strftime('%Y%m%d')}.parquet"
            )

        # 确定获取数据的时间范围
        if force_days:
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=force_days)).strftime(
                "%Y%m%d"
            )
            print(f"📊 {code} - 获取最近 {force_days} 天数据...")
            # 必须指定足够大的 count，否则默认 100 条
            rows = await self.fetch_kline(code, start_date, end_date, count=5000)
        else:
            last_date = self._get_last_trade_date(symbol)

            if last_date:
                start_dt = datetime.strptime(str(last_date), "%Y%m%d") + timedelta(
                    days=1
                )
                start_date = start_dt.strftime("%Y%m%d")
                end_date = datetime.now().strftime("%Y%m%d")

                if int(start_date) > int(end_date):
                    print(f"✅ {code} - 已是最新 ({last_date})")
                    return False

                print(f"📊 {code} - 增量更新 {start_date} ~ {end_date}...")
                rows = await self.fetch_kline(code, start_date, end_date, count=5000)
            else:
                print(f"📊 {code} - 首次获取 (从 20200101)...")
                start_date = "20200101"
                end_date = datetime.now().strftime("%Y%m%d")
                rows = await self.fetch_kline(code, start_date, end_date, count=5000)

        if not rows:
            print(f"⚠️  {code} - 无新数据")
            return False

        new_df = pd.DataFrame(rows)

        if parquet_file.exists():
            try:
                old_df = pd.read_parquet(parquet_file)
                for col in new_df.columns:
                    if col not in old_df.columns:
                        old_df[col] = None

                combined_df = pd.concat([old_df, new_df], ignore_index=True)
                combined_df = (
                    combined_df.drop_duplicates(subset=["trade_date"], keep="last")
                    .sort_values("trade_date")
                    .reset_index(drop=True)
                )

                new_rows = len(combined_df) - len(old_df)
                print(f"✅ {code} - 新增 {new_rows} 条，总计 {len(combined_df)} 条")

            except Exception as e:
                print(f"⚠️  {code} - 合并数据失败，使用新数据: {e}")
                combined_df = new_df
        else:
            combined_df = new_df
            print(f"✅ {code} - 新建文件，{len(combined_df)} 条记录")

        if not combined_df.empty:
            min_date = combined_df["trade_date"].min()
            max_date = combined_df["trade_date"].max()
            new_filename = f"{code}_daily_{min_date}_{max_date}.parquet"
            new_path = self.data_dir / new_filename

            if parquet_file.exists() and parquet_file.name != new_filename:
                parquet_file.unlink()
                print(f"   重命名: {parquet_file.name} -> {new_filename}")

            combined_df.to_parquet(new_path, index=False)

        return True

    async def update_batch(
        self, symbols: List[str], exchange: str = "SH", force_days: Optional[int] = None
    ):
        """批量更新多个ETF"""
        total = len(symbols)
        success = 0

        print(f"\n开始更新 {total} 个ETF...")
        print(f"数据目录: {self.data_dir.absolute()}")
        print("=" * 60)

        for idx, symbol in enumerate(symbols, 1):
            print(f"\n[{idx}/{total}] ", end="")

            # 尝试 SH 和 SZ
            # 如果用户没有指定 exchange，或者我们不知道 exchange，可以尝试两个
            # 这里简单起见，先试 SH，如果失败或无数据，再试 SZ？
            # 或者根据 symbol 前缀判断：51/58 -> SH, 15 -> SZ

            current_exchange = exchange
            if symbol.startswith("5"):
                current_exchange = "SH"
            elif symbol.startswith("1"):
                current_exchange = "SZ"

            if await self.update_symbol(symbol, current_exchange, force_days):
                success += 1

            if idx < total:
                await asyncio.sleep(0.5)

        print("\n" + "=" * 60)
        print(f"✅ 更新完成: {success}/{total} 成功")


def load_config(config_file: Path) -> List[str]:
    """从配置文件加载ETF列表"""
    if not config_file.exists():
        print(f"❌ 配置文件不存在: {config_file}")
        return []

    if config_file.suffix == ".json":
        with open(config_file, "r") as f:
            data = json.load(f)
            return data.get("symbols", [])
    elif config_file.suffix in [".yaml", ".yml"]:
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)
            symbols = set()

            # 1. 尝试从 pools 中提取 (etf_pools.yaml 结构)
            if isinstance(data, dict) and "pools" in data:
                pools = data["pools"]
                for pool_name, pool_data in pools.items():
                    if isinstance(pool_data, dict) and "symbols" in pool_data:
                        symbols.update(pool_data["symbols"])

            # 2. 尝试直接从 symbols 字段提取 (combo_wfo_config.yaml 结构)
            if isinstance(data, dict) and "symbols" in data:
                if isinstance(data["symbols"], list):
                    symbols.update(data["symbols"])

            # 3. 尝试顶层列表
            if isinstance(data, list):
                symbols.update(data)

            return list(symbols)
    else:
        with open(config_file, "r") as f:
            return [line.strip() for line in f if line.strip()]


async def main():
    parser = argparse.ArgumentParser(
        description="基于 QMT Bridge SDK 的 ETF 日线数据增量更新"
    )
    parser.add_argument("--symbols", type=str, help="ETF代码，逗号分隔")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--all", action="store_true", help="更新配置文件中的所有ETF")
    parser.add_argument("--host", type=str, default="localhost")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--data-dir", type=str, default="./raw/ETF/daily")
    parser.add_argument("--exchange", type=str, default="SH")
    parser.add_argument("--force-days", type=int, help="强制获取最近N天数据")

    args = parser.parse_args()

    symbols = []
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    elif args.config:
        symbols = load_config(Path(args.config))
    elif args.all:
        # 优先尝试 etf_pools.yaml
        pool_config = Path("configs/etf_pools.yaml")
        if pool_config.exists():
            print(f"📚 加载配置: {pool_config}")
            symbols = load_config(pool_config)
        else:
            default_config = Path("etf_list.json")
            if default_config.exists():
                print(f"📚 加载配置: {default_config}")
                symbols = load_config(default_config)
            else:
                print("❌ 未找到配置文件")
                return
    else:
        parser.print_help()
        return

    if not symbols:
        print("❌ 没有要更新的ETF")
        return

    updater = ETFDataUpdater(host=args.host, port=args.port, data_dir=args.data_dir)
    await updater.update_batch(
        symbols=symbols, exchange=args.exchange, force_days=args.force_days
    )

    # ✅ FIX: 清理缓存，确保下次加载使用最新数据
    # 即使 data_loader.py 已改用 mtime，这里作为双保险
    import shutil
    cache_dir = Path(__file__).parent.parent / "src" / "etf_strategy" / ".cache"
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            print(f"✅ 已清理缓存: {cache_dir}")
        except Exception as e:
            print(f"⚠️  清理缓存失败（可忽略）: {e}")


if __name__ == "__main__":
    asyncio.run(main())
