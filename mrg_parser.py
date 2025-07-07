#!/usr/bin/env python3
"""
Simple MRG Track Parser for Gravity Defied
Extracts raw coordinate points from .mrg files
"""

import struct
import json
import csv
from typing import List, Tuple, Dict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Track:
    """Represents a single track with its raw coordinates"""
    name: str
    level: int
    track_id: int
    start_x: int
    start_y: int
    finish_x: int
    finish_y: int
    points: List[Tuple[int, int]]

    def __post_init__(self):
        """Convert coordinates using the game's transformation"""
        # Apply coordinate transformation: (x << 16) >> 3
        self.start_x = (self.start_x << 16) >> 3
        self.start_y = (self.start_y << 16) >> 3
        self.finish_x = (self.finish_x << 16) >> 3
        self.finish_y = (self.finish_y << 16) >> 3

        # Transform all points: (x << 3) >> 16
        self.points = [((x << 3) >> 16, (y << 3) >> 16) for x, y in self.points]


class MRGParser:
    """Simple parser for Gravity Defied MRG files"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.tracks: List[Track] = []

    def parse(self) -> List[Track]:
        """Parse the MRG file and return list of tracks with raw coordinates"""
        with open(self.file_path, 'rb') as f:
            # Read header for 3 levels
            levels_data = []

            for level in range(3):
                # Read track count for this level
                track_count = struct.unpack('>I', f.read(4))[0]  # Big endian int

                level_tracks = []
                for track_id in range(track_count):
                    # Read track metadata
                    offset = struct.unpack('>I', f.read(4))[0]

                    # Read track name (null-terminated string)
                    name_bytes = b""
                    while True:
                        byte = f.read(1)
                        if byte == b'\x00':
                            break
                        name_bytes += byte

                    name = name_bytes.decode('cp1251', errors='ignore').replace('_', ' ')
                    level_tracks.append((offset, name, track_id))

                levels_data.append(level_tracks)

            # Now read track data at each offset
            for level, level_tracks in enumerate(levels_data):
                for offset, name, track_id in level_tracks:
                    f.seek(offset)
                    track = self._parse_track(f, name, level, track_id)
                    if track:
                        self.tracks.append(track)

        return self.tracks

    def _parse_track(self, f, name: str, level: int, track_id: int) -> Track:
        """Parse individual track data"""
        try:
            # Check track marker
            marker = struct.unpack('B', f.read(1))[0]
            if marker != 0x33:
                print(f"Warning: Invalid track marker {marker:02x} for {name}")
                return None

            # Read track properties
            start_x = struct.unpack('>i', f.read(4))[0]
            start_y = struct.unpack('>i', f.read(4))[0]
            finish_x = struct.unpack('>i', f.read(4))[0]
            finish_y = struct.unpack('>i', f.read(4))[0]
            points_count = struct.unpack('>H', f.read(2))[0]  # Short

            # Read first point
            first_x = struct.unpack('>i', f.read(4))[0]
            first_y = struct.unpack('>i', f.read(4))[0]

            points = [(first_x, first_y)]
            current_x = first_x
            current_y = first_y

            # Read remaining points
            for i in range(1, points_count):
                x_offset = struct.unpack('b', f.read(1))[0]  # Signed byte

                if x_offset == -1:
                    # Reset coordinates and read full int coordinates
                    current_x = current_y = 0
                    x = struct.unpack('>i', f.read(4))[0]
                    y = struct.unpack('>i', f.read(4))[0]
                else:
                    # Read y offset and add to current position
                    y_offset = struct.unpack('b', f.read(1))[0]  # Signed byte
                    x = x_offset
                    y = y_offset

                current_x += x
                current_y += y
                points.append((current_x, current_y))

            return Track(name, level, track_id, start_x, start_y,
                         finish_x, finish_y, points)

        except Exception as e:
            print(f"Error parsing track {name}: {e}")
            return None


def save_tracks_csv(tracks: List[Track], output_file: str):
    """Save tracks to CSV with one row per track"""
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Header
        writer.writerow(['name', 'level', 'track_id', 'start_x', 'start_y',
                         'finish_x', 'finish_y', 'point_count', 'points_x', 'points_y'])

        for track in tracks:
            points_x = [str(p[0]) for p in track.points]
            points_y = [str(p[1]) for p in track.points]

            writer.writerow([
                track.name,
                track.level,
                track.track_id,
                track.start_x,
                track.start_y,
                track.finish_x,
                track.finish_y,
                len(track.points),
                '|'.join(points_x),  # Pipe-separated coordinates
                '|'.join(points_y)
            ])


def save_tracks_json(tracks: List[Track], output_file: str):
    """Save tracks to JSON with full structure"""
    track_data = []

    for track in tracks:
        track_dict = {
            'name': track.name,
            'level': track.level,
            'track_id': track.track_id,
            'start_x': track.start_x,
            'start_y': track.start_y,
            'finish_x': track.finish_x,
            'finish_y': track.finish_y,
            'points': track.points
        }
        track_data.append(track_dict)

    with open(output_file, 'w', encoding='utf-8') as jsonfile:
        json.dump(track_data, jsonfile, indent=2, ensure_ascii=False)


def main():
    """Main function"""
    import sys

    if len(sys.argv) != 2:
        print("Usage: python mrg_parser.py <path_to_levels.mrg>")
        return

    mrg_file = sys.argv[1]

    # Parse MRG file
    parser = MRGParser(mrg_file)
    tracks = parser.parse()

    print(f"Parsed {len(tracks)} tracks from {mrg_file}")

    # Print summary
    for track in tracks:
        print(f"  {track.name} (Level {track.level}, {len(track.points)} points)")

    # Save raw data
    base_name = Path(mrg_file).stem

    csv_file = f"{base_name}_tracks.csv"
    save_tracks_csv(tracks, csv_file)
    print(f"\nTrack data saved to {csv_file}")

    json_file = f"{base_name}_tracks.json"
    save_tracks_json(tracks, json_file)
    print(f"Track data saved to {json_file}")


if __name__ == "__main__":
    main()