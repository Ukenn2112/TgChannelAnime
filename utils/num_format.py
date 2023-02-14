from typing import Union


async def volume_format(volume: str) -> Union[int, float]:
    """格式化剧集集数"""
    try:
        if volume.isdigit():
            volume = int(volume)
        elif volume[:-1].isdecimal():
            volume = float(f"{volume[:-1]}.5")
        elif "." in volume:
            volume = float(volume)
        else:
            volume = 1
    except:
        volume = 1