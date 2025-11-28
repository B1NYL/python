import subprocess
import sys

def install_if_missing(package):
    try:
        __import__(package)
    except ImportError:
        print(f"[설치] '{package}' 패키지가 없어 설치합니다...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"[설치 완료] {package}")

install_if_missing("pygame")
install_if_missing("numpy")
install_if_missing("sounddevice")
install_if_missing("soundfile")
install_if_missing("pytmx")

import pygame
import math
import random
import os
import platform
from pytmx.util_pygame import load_pygame
import sounddevice as sd
import soundfile as sf
import numpy as np
import time


MAP_SCALE = 2
PLAYER_SCALE = 2
BASE_PLAYER_SIZE = 40
DUMMY_SCALE = 1.2
PLAYER_SIZE = BASE_PLAYER_SIZE * PLAYER_SCALE

pygame.init()
pygame.mixer.init(frequency=44100, channels=2)
VOLUME = 0.5
pygame.mixer.music.set_volume(VOLUME)
SPELL_SOUND_DIR = "spell_sounds"
os.makedirs(SPELL_SOUND_DIR, exist_ok=True)

WIDTH, HEIGHT = 1600, 1200
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Voice RPG")
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
PURPLE = (150, 0, 255)
YELLOW = (255, 255, 0)
DARK_RED = (139, 0, 0)
DARK_GREEN = (0, 100, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
BROWN = (139, 69, 19)

BOOK_IMAGE = None
if os.path.exists("img/book.png"):
    try:
        img = pygame.image.load("img/book.png").convert_alpha()
        BOOK_IMAGE = pygame.transform.scale(img, (36, 36))
        print("[DEBUG] book.png 로드 완료")
    except Exception as e:
        print(f"[DEBUG] book.png 로드 실패: {e}")
else:
    print("[DEBUG] img/book.png 를 찾을 수 없습니다.")

SLIME_STAND_FRAMES = []
SLIME_STAND_DELAYS = [200, 300, 250]
SLIME_DIE_FRAMES = []
SLIME_DIE_DELAYS = [70] * 13


def load_slime_frames():
    global SLIME_STAND_FRAMES, SLIME_DIE_FRAMES
    SLIME_STAND_FRAMES = []
    SLIME_DIE_FRAMES = []
    base_size = int(30 * PLAYER_SCALE)
    for i in range(1, 4):
        path = f"img/slime_stand_{i}.png"
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            width = int(base_size * 1.3)
            height = base_size
            img = pygame.transform.scale(img, (width, height))
            SLIME_STAND_FRAMES.append(img)

    for i in range(1, 14):
        path = f"img/slime_die_{i}.png"
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            width = int(base_size * 1.3)
            height = base_size
            img = pygame.transform.scale(img, (width, height))
            SLIME_DIE_FRAMES.append(img)

#GPT
def get_korean_font(size):
    system = platform.system()
    local_candidates = [
        "fonts/NotoSansKR-Regular.otf",
        "fonts/NotoSansKR-Regular.ttf",
        "fonts/NanumGothic.ttf",
        "fonts/NanumGothic.otf",
        "NotoSansKR-Regular.otf",
        "NotoSansKR-Regular.ttf",
        "NanumGothic.ttf",
        "NanumGothic.otf",
    ]
    for p in local_candidates:
        if os.path.exists(p):
            try:
                return pygame.font.Font(p, size)
            except:
                pass
    font_paths = []
    font_names = []
    if system == "Windows":
        font_paths = [
            "C:/Windows/Fonts/malgun.ttf",
            "C:/Windows/Fonts/malgunbd.ttf",
            "C:/Windows/Fonts/gulim.ttc",
            "C:/Windows/Fonts/batang.ttc",
        ]
        font_names = ['맑은 고딕', 'Malgun Gothic', '굴림', '돋움']
    elif system == "Linux":
        font_paths = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            os.path.expanduser("~/.fonts/NanumGothic.ttf"),
        ]
        font_names = ['NanumGothic', 'UnDotum']
    elif system == "Darwin":
        font_paths = ["/System/Library/Fonts/AppleSDGothicNeo.ttc"]
        font_names = ['Apple SD Gothic Neo']

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return pygame.font.Font(font_path, size)
            except:
                pass
    for font_name in font_names:
        try:
            font = pygame.font.SysFont(font_name, size)
            font.render("한글", True, WHITE)
            return font
        except:
            pass
    print("경고: 한글 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")
    return pygame.font.Font(None, size)


def load_character_images(gender, size=PLAYER_SIZE):
    images = {'right': [], 'left': [], 'up': [], 'down': []}
    directions = ['right', 'left', 'up', 'down']
    prefix = 'man' if gender == 'male' else 'woman'
    for direction in directions:
        for i in [1, 2, 3, 2]:
            filename = f"img/{prefix}_{direction}_{i}.png"
            if os.path.exists(filename):
                img = pygame.image.load(filename).convert_alpha()
                images[direction].append(pygame.transform.scale(img, (size, size)))
            else:
                img = pygame.Surface((size, size), pygame.SRCALPHA)
                color = BLUE if gender == 'male' else (255, 105, 180)
                img.fill(color)
                images[direction].append(img)
    return images



class Camera:
    def __init__(self, width, height):
        self.width, self.height, self.x, self.y = width, height, 0, 0
        self.offset_x = 0
        self.offset_y = 0

    def update(self, target):
        self.x = int(target.x - WIDTH // 2 + target.width // 2)
        self.y = int(target.y - HEIGHT // 2 + target.height // 2)

    #보정
    def apply(self, entity):
        return int(entity.x - self.x + self.offset_x), int(entity.y - self.y + self.offset_y)


    def apply_pos(self, x, y):
        return int(x - self.x + self.offset_x), int(y - self.y + self.offset_y)


#GPT작성
class TiledMap:
    def __init__(self, tmx_path, map_scale=MAP_SCALE):
        self.tmx, self.scale = load_pygame(tmx_path), map_scale
        self.tile_w, self.tile_h = self.tmx.tilewidth, self.tmx.tileheight
        self.stile_w, self.stile_h = self.tile_w * self.scale, self.tile_h * self.scale
        self.map_w_tiles, self.map_h_tiles = self.tmx.width, self.tmx.height
        self.pixel_w, self.pixel_h = self.map_w_tiles * self.stile_w, self.map_h_tiles * self.stile_h
        self.blocked, self._scaled_cache = set(), {}
        for layer in self.tmx.visible_layers:
            if hasattr(layer, "data"):
                layer_collides = bool(getattr(layer, "properties", {}).get("collision", False))
                for x, y, gid in layer.iter_data():
                    if gid != 0:
                        props = self.tmx.get_tile_properties_by_gid(gid) or {}
                        if layer_collides or props.get("collide", False) or props.get("collision", False):
                            self.blocked.add((x, y))

    def _get_scaled(self, image):
        if self.scale == 1:
            return image
        key = id(image)
        if key in self._scaled_cache:
            return self._scaled_cache[key]
        scaled = pygame.transform.scale(
            image, (int(image.get_width() * self.scale), int(image.get_height() * self.scale))
        )
        self._scaled_cache[key] = scaled
        return scaled

    def clamp_camera(self, camera):
        if self.pixel_w <= WIDTH:
            camera.x = -(WIDTH - self.pixel_w) // 2
        else:
            camera.x = max(0, min(int(camera.x), self.pixel_w - WIDTH))
        if self.pixel_h <= HEIGHT:
            camera.y = -(HEIGHT - self.pixel_h) // 2
        else:
            camera.y = max(0, min(int(camera.y), self.pixel_h - HEIGHT))

    def draw(self, surface, camera):
        start_tx = max(0, int(camera.x // self.stile_w))
        start_ty = max(0, int(camera.y // self.stile_h))
        end_tx = min(self.map_w_tiles, int((camera.x + WIDTH) // self.stile_w) + 1)
        end_ty = min(self.map_h_tiles, int((camera.y + HEIGHT) // self.stile_h) + 1)
        for layer in self.tmx.visible_layers:
            if hasattr(layer, "tiles"):
                for x, y, image in layer.tiles():
                    if start_tx <= x < end_tx and start_ty <= y < end_ty and image:
                        screen_x, screen_y = camera.apply_pos(
                            x * self.stile_w, y * self.stile_h
                        )
                        surface.blit(self._get_scaled(image), (screen_x, screen_y))

    def rect_blocked(self, rect):
        if rect.right < 0 or rect.left >= self.pixel_w or rect.bottom < 0 or rect.top >= self.pixel_h:
            return True
        left = max(0, int(rect.left // self.stile_w))
        right = min(self.map_w_tiles - 1, int(rect.right // self.stile_w))
        top = max(0, int(rect.top // self.stile_h))
        bottom = min(self.map_h_tiles - 1, int(rect.bottom // self.stile_h))
        for tx in range(left, right + 1):
            for ty in range(top, bottom + 1):
                if (tx, ty) in self.blocked:
                    if rect.colliderect(pygame.Rect(tx * self.stile_w, ty * self.stile_h, self.stile_w, self.stile_h)):
                        return True
        return False

    def find_player_spawn(self):
        for layer in self.tmx.layers:
            if not hasattr(layer, "objects"):
                continue
            layer_name = getattr(layer, "name", "")
            for obj in layer.objects:
                props = getattr(obj, "properties", {}) or {}
                name = (getattr(obj, "name", "") or "").lower()
                spawn_type = str(props.get("spawn_type", "")).lower()
                if name == "player_spawn" or spawn_type == "player":
                    x = int(obj.x * self.scale)
                    y = int(obj.y * self.scale)
                    print(f"[DEBUG] 플레이어 스폰 발견: layer='{layer_name}', name='{name}', spawn_type='{spawn_type}', pos=({x},{y})")
                    return x, y
        print("[DEBUG] 플레이어 스폰 오브젝트를 찾지 못했습니다. (0,0)을 사용합니다.")
        return 0, 0

    def find_enemy_spawns(self):
        spawns = []
        for layer in self.tmx.layers:
            layer_name = getattr(layer, "name", "")
            lname = layer_name.lower()
            print(f"[DEBUG] 레이어 확인: {layer_name}")
            if "enemies" in lname:
                if hasattr(layer, "objects"):
                    print(f"[DEBUG] Enemies 레이어에서 {len(layer.objects)}개의 오브젝트 발견")
                    for obj in layer.objects:
                        props = getattr(obj, "properties", {}) or {}
                        raw_type = props.get('enemy_type', getattr(obj, "name", "slime"))
                        enemy_type = str(raw_type).strip().lower()
                        raw_level = props.get("level", props.get("enemy_level", 1))
                        try:
                            level = int(raw_level)
                        except (TypeError, ValueError):
                            level = 1
                        ex = int(obj.x * self.scale)
                        ey = int(obj.y * self.scale)
                        spawns.append((ex, ey, enemy_type, level))
                        print(f"[DEBUG] 적 스폰: type={enemy_type}, level={level}, pos=({ex}, {ey})")
                else:
                    try:
                        objs = list(layer)
                        print(f"[DEBUG] Enemies 레이어(iter)에서 {len(objs)}개의 오브젝트 발견")
                        for obj in objs:
                            props = getattr(obj, "properties", {}) or {}
                            raw_type = props.get('enemy_type', getattr(obj, "name", "slime"))
                            enemy_type = str(raw_type).strip().lower()
                            raw_level = props.get("level", props.get("enemy_level", 1))
                            try:
                                level = int(raw_level)
                            except (TypeError, ValueError):
                                level = 1
                            ex = int(obj.x * self.scale)
                            ey = int(obj.y * self.scale)
                            spawns.append((ex, ey, enemy_type, level))
                            print(f"[DEBUG] 적 스폰: type={enemy_type}, level={level}, pos=({ex}, {ey})")
                    except TypeError:
                        print("[DEBUG] Enemies 레이어를 순회할 수 없습니다.")
        print(f"[DEBUG] 총 {len(spawns)}개의 적 스폰 위치 발견")
        return spawns

    def find_portals(self):
        portals = []
        for layer in self.tmx.layers:
            if hasattr(layer, "tiles") or hasattr(layer, "data"):
                continue
            try:
                iterator = iter(layer)
            except TypeError:
                continue
            for obj in iterator:
                props = getattr(obj, "properties", {}) or {}
                if "portal_type" not in props:
                    continue
                portal_type = str(props.get("portal_type", "")).strip()
                w = int(getattr(obj, "width", 50) * self.scale) or 50
                h = int(getattr(obj, "height", 100) * self.scale) or 100
                rect = pygame.Rect(
                    int(obj.x * self.scale),
                    int(obj.y * self.scale),
                    w, h
                )
                portals.append({
                    "rect": rect,
                    "portal_type": portal_type
                })
        print(f"[DEBUG] TMX 포탈 개수: {len(portals)}")
        for p in portals:
            print(f"  portal_type={p['portal_type']}, rect={p['rect']}")
        return portals



class DamageText:
    def __init__(self, x, y, damage, critical=False):
        self.x = x
        self.y = y
        self.damage = damage
        self.critical = critical
        self.lifetime = 60
        self.active = True
        self.offset_y = 0


    def update(self):
        self.lifetime -= 1
        self.offset_y -= 1.5
        if self.lifetime <= 0:
            self.active = False

    def draw(self, surface, camera):
        if not self.active:
            return
        sx, sy = camera.apply_pos(self.x, self.y + self.offset_y)
        if self.critical:
            font = get_korean_font(32)
            color = RED
            text = f"{int(self.damage)}!"
        else:
            font = get_korean_font(24)
            color = WHITE
            text = f"{int(self.damage)}"
        alpha = int(255 * (self.lifetime / 60))
        text_surf = font.render(text, True, color)
        text_surf.set_alpha(alpha)
        text_rect = text_surf.get_rect(center=(int(sx), int(sy)))
        surface.blit(text_surf, text_rect)


class Player:
    def __init__(self, x, y, gender='male'):
        self.x, self.y = x, y
        self.width, self.height = PLAYER_SIZE, PLAYER_SIZE
        self.speed = 5
        self.max_hp, self.hp = 100, 100
        self.max_mp, self.mp = 100, 100
        self.mp_regen = 0.5
        self.images = load_character_images(gender, size=self.width)
        self.current_direction = 'down'
        self.current_frame = 1
        self.animation_counter = 0
        self.animation_speed = 10
        self.is_moving = False
        self.level = 1
        self.xp = 0
        self.xp_to_next = 100
        self.inventory = {
            "HP 포션": 3,
        }
        self.known_spells = {}
        self.equipped_spells = []
        self.weapon = "맨손"

        self.known_spells["iceberg"] = "S"
        self.equipped_spells.append("iceberg")
        self.known_spells["meteor"] = "S"
        self.equipped_spells.append("meteor")
        self.known_spells["thunder"] = "S"
        self.equipped_spells.append("thunder")
        self.known_spells["backflow"] = "S"
        self.equipped_spells.append("backflow")

        self.known_spells["fireball"] = "C"
        self.equipped_spells.append("fireball")
        self.known_spells["ice_lans"] = "C"
        self.equipped_spells.append("ice_lans")
        self.known_spells["lightning_bolt"] = "C"
        self.equipped_spells.append("lightning_bolt")
        self.known_spells["water_blast"] = "C"
        self.equipped_spells.append("water_blast")

        self.spell_sounds = {}

    def move(self, keys, game_map):
        self.is_moving = False
        move_speed = self.speed * (1.5 if keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL] else 1.0)
        vx, vy = 0, 0
        moving_direction = None
        if keys[pygame.K_w]:
            vy -= move_speed
            moving_direction = 'up'
        if keys[pygame.K_s]:
            vy += move_speed
            moving_direction = moving_direction or 'down'
        if keys[pygame.K_a]:
            vx -= move_speed
            moving_direction = moving_direction or 'left'
        if keys[pygame.K_d]:
            vx += move_speed
            moving_direction = moving_direction or 'right'
        if vx != 0 and vy != 0:
            vx *= 0.707 
            vy *= 0.707
        if vx != 0 or vy != 0:
            self.is_moving = True
            if game_map:
                if not game_map.rect_blocked(pygame.Rect(self.x + vx, self.y, self.width, self.height)):
                    self.x += vx
                if not game_map.rect_blocked(pygame.Rect(self.x, self.y + vy, self.width, self.height)):
                    self.y += vy
            else:
                self.x += vx
                self.y += vy
        if moving_direction:
            self.current_direction = moving_direction
        if self.is_moving:
            self.animation_counter += 1
            if self.animation_counter >= self.animation_speed:
                self.animation_counter = 0
                self.current_frame = (self.current_frame + 1) % 4
        else:
            self.current_frame = 1

    def regen_mp(self):
        self.mp = min(self.max_mp, self.mp + self.mp_regen)

    def add_xp(self, amount):
        self.xp += amount
        print(f"[XP] 경험치 +{amount} (현재 {self.xp}/{self.xp_to_next})")
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            hp_increase = 20
            mp_increase = 10
            self.max_hp += hp_increase
            self.max_mp += mp_increase
            self.hp = self.max_hp
            self.mp = self.max_mp
            self.xp_to_next = int(self.xp_to_next * 1.2)
            print(f"[레벨업] LV {self.level} 달성! HP+{hp_increase}, MP+{mp_increase}")
            print(f"[레벨업] 다음 레벨까지: {self.xp_to_next} EXP")

    def cast_spell(self, target_world_pos, spell_type="fireball", current_map=None):
        if spell_type not in self.known_spells:
            print("아직 배우지 않은 마법입니다.")
            return None

        # MP 소모량 설정
        if spell_type == "fireball":
            mp_cost = 20
        elif spell_type == "ice_lans":
            mp_cost = 22
        elif spell_type == "lightning_bolt":
            mp_cost = 30
        elif spell_type == "water_blast":
            mp_cost = 22
        elif spell_type == "meteor":
            mp_cost = 60
        elif spell_type == "thunder":
            mp_cost = 100
        elif spell_type == "iceberg":
            mp_cost = 80
        elif spell_type == "backflow":
            mp_cost = 75
        else:
            mp_cost = 20

        if self.mp < mp_cost:
            print("MP 부족!")
            return None
        self.mp -= mp_cost


        sound = self.spell_sounds.get(spell_type)
        if sound is not None:
            sound.play()

        #마법 시작 좌표.
        sx = self.x + self.width // 2
        sy = self.y + self.height // 2
        dx = target_world_pos[0] - sx
        dy = target_world_pos[1] - sy
        dist = math.hypot(dx, dy)


        if spell_type in ("meteor", "thunder", "iceberg", "backflow") and current_map is not None:
            center_x, center_y = target_world_pos

            if spell_type == "meteor":
                radius = 140
                base_damage = 80
                extra = {
                    "damage": base_damage,
                    "start_pos": (sx, sy),
                }
                current_map.area_effects.append(
                    AreaEffect("meteor", center_x, center_y, radius, extra=extra)
                )
                print("[S-스킬] 메테오 시전")

            elif spell_type == "thunder":
                radius = 200
                base_damage = 70
                extra = {"damage": base_damage}
                current_map.area_effects.append(
                    AreaEffect("thunder", center_x, center_y, radius, extra=extra)
                )
                print("[S-스킬] 천둥 시전")

            elif spell_type == "iceberg":
                radius = 130
                base_damage = 60
                extra = {"damage": base_damage, "freeze_time": 240}
                current_map.area_effects.append(
                    AreaEffect("iceberg", center_x, center_y, radius, extra=extra)
                )
                print("[S-스킬] 빙산 시전")

            elif spell_type == "backflow":
                if dist == 0:
                    return None
                max_range = 450
                cone_half_angle = math.radians(60)
                dir_x = dx / dist
                dir_y = dy / dist
                base_damage = 50
                for enemy in current_map.enemies:
                    ex = enemy.x + enemy.width / 2
                    ey = enemy.y + enemy.height / 2
                    vx = ex - sx
                    vy = ey - sy
                    enemy_dist = math.hypot(vx, vy)
                    if enemy_dist <= 0 or enemy_dist > max_range:
                        continue
                    nvx = vx / enemy_dist
                    nvy = vy / enemy_dist
                    dot = nvx * dir_x + nvy * dir_y
                    dot = max(-1.0, min(1.0, dot))
                    angle = math.acos(dot)
                    if angle <= cone_half_angle:
                        enemy.hp -= base_damage
                        current_map.damage_texts.append(
                            DamageText(ex, enemy.y, base_damage)
                        )
                        enemy.apply_slow(duration=360)
                extra = ((sx, sy), (dir_x, dir_y), cone_half_angle)
                current_map.area_effects.append(
                    AreaEffect("backflow", center_x, center_y, max_range, extra=extra)
                )
                print("[S-스킬] 역류 시전")

            return None

        # ---------- 기존 C급 투사체 마법 ----------
        if dist > 0:
            return Spell(sx, sy, dx / dist, dy / dist, spell_type, dist)
        return None

    def draw(self, surface, camera):
        screen_x, screen_y = camera.apply(self)
        surface.blit(self.images[self.current_direction][self.current_frame], (screen_x, screen_y))
        pygame.draw.rect(surface, DARK_RED, (screen_x + 15, screen_y - 15, 50, 5))
        pygame.draw.rect(surface, RED, (screen_x + 15, screen_y - 15, 50 * max(0, self.hp / self.max_hp), 5))
        pygame.draw.rect(surface, DARK_GREEN, (screen_x + 15, screen_y - 8, 50, 5))
        pygame.draw.rect(surface, GREEN, (screen_x + 15, screen_y - 8, 50 * max(0, self.mp / self.max_mp), 5))



class LightningChain:
    def __init__(self, x, y, damage, hit_enemies, max_lifetime=180):
        self.x = x
        self.y = y
        self.chain_x = x
        self.chain_y = y
        self.damage = damage
        self.hit_enemies = hit_enemies
        self.lifetime = max_lifetime
        self.active = True
        self.chain_delay = 0
        self.chain_delay_max = 10
        self.just_chained = False

    def update(self, enemies, damage_texts):
        if not self.active:
            return
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.active = False
            return
        self.chain_delay -= 1
        self.just_chained = False
        if self.chain_delay > 0:
            return
        closest_enemy = None
        closest_dist = 250
        for enemy in enemies:
            if id(enemy) in self.hit_enemies:
                continue
            if hasattr(enemy, 'dying') and enemy.dying:
                continue
            if hasattr(enemy, 'is_dummy') and enemy.is_dummy:
                pass
            elif enemy.hp <= 0:
                continue
            ex = enemy.x + enemy.width / 2
            ey = enemy.y + enemy.height / 2
            dist = math.hypot(ex - self.x, ey - self.y)
            if dist < closest_dist:
                closest_dist = dist
                closest_enemy = enemy
        if closest_enemy:
            self.chain_x = self.x
            self.chain_y = self.y
            closest_enemy.hp -= self.damage
            self.hit_enemies.append(id(closest_enemy))
            damage_texts.append(DamageText(
                closest_enemy.x + closest_enemy.width / 2,
                closest_enemy.y,
                self.damage
            ))
            self.x = closest_enemy.x + closest_enemy.width / 2
            self.y = closest_enemy.y + closest_enemy.height / 2
            self.chain_delay = self.chain_delay_max
            self.just_chained = True

    def draw(self, surface, camera):
        if not self.active:
            return
        sx, sy = camera.apply_pos(self.x, self.y)
        if self.chain_x != self.x or self.chain_y != self.y:
            chain_sx, chain_sy = camera.apply_pos(self.chain_x, self.chain_y)
            segments = 8
            points = []
            for i in range(segments + 1):
                t = i / segments
                #각 점
                mid_x = chain_sx + (sx - chain_sx) * t
                mid_y = chain_sy + (sy - chain_sy) * t
                dx = sx - chain_sx
                dy = sy - chain_sy
                length = math.hypot(dx, dy)
                #중간에 수직 넣기
                if length > 0:
                    perp_x = -dy / length
                    perp_y = dx / length
                    #흔들기
                    offset = random.uniform(-10, 10)
                    mid_x += perp_x * offset
                    mid_y += perp_y * offset
                points.append((int(mid_x), int(mid_y)))
            if len(points) >= 2:
                pygame.draw.lines(surface, (255, 255, 100), False, points, 4)
                pygame.draw.lines(surface, (255, 255, 255), False, points, 2)
        radius = 8 + int(3 * math.sin(pygame.time.get_ticks() / 100))
        pygame.draw.circle(surface, (255, 255, 180), (int(sx), int(sy)), radius)
        pygame.draw.circle(surface, YELLOW, (int(sx), int(sy)), radius - 2)
        for _ in range(3):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(10, 20)
            px = sx + math.cos(angle) * dist
            py = sy + math.sin(angle) * dist
            pygame.draw.line(surface, (255, 255, 200), (int(sx), int(sy)), (int(px), int(py)), 1)


class AreaEffect:
    def __init__(self, effect_type, x, y, size, extra=None):
        self.effect_type = effect_type
        self.x = x
        self.y = y
        self.size = size
        self.extra = extra or {}
        self.age = 0
        self.active = True

        if effect_type == "meteor":
            self.max_lifetime = 60
            self.impact_frame = 25
            self.impact_done = False
        elif effect_type == "thunder":
            self.max_lifetime = 70
            self.base_damage = self.extra.get("damage", 70)
            self.strike_count = 25
            self.strike_interval = 6
            self.strike_radius = int(self.size * 0.4)
            self.strikes = []
            for i in range(self.strike_count):
                angle = random.uniform(0, math.pi * 2)
                r = random.uniform(self.size * 0.3, self.size * 1.5)
                sx = self.x + math.cos(angle) * r
                sy = self.y + math.sin(angle) * r
                self.strikes.append({
                    "x": sx,
                    "y": sy,
                    "start": 5 + i * self.strike_interval,
                    "hit": False,
                })
        elif effect_type == "iceberg":
            self.max_lifetime = 60
            self.base_damage = self.extra.get("damage", 60)
            self.freeze_time = self.extra.get("freeze_time", 240)
            self.hit_enemies = set()
        elif effect_type == "backflow":
            self.max_lifetime = 35
        else:
            self.max_lifetime = 45

    def update(self, game_map):
        self.age += 1
        if self.effect_type == "meteor" and not self.impact_done:
            if self.age == self.impact_frame:
                base_damage = self.extra.get("damage", 80)
                radius = self.size
                for enemy in game_map.enemies:
                    ex = enemy.x + enemy.width / 2
                    ey = enemy.y + enemy.height / 2
                    if math.hypot(ex - self.x, ey - self.y) <= radius:
                        enemy.hp -= base_damage
                        game_map.damage_texts.append(
                            DamageText(ex, enemy.y, base_damage, critical=True)
                        )
                        enemy.apply_burn(duration=600, total_damage=120)
                        enemy.apply_slow(duration=300)
                self.impact_done = True

        # ----- 천둥: 순차적 낙뢰 판정 -----
        elif self.effect_type == "thunder":
            for s in self.strikes:
                if not s["hit"] and self.age == s["start"]:
                    sx = s["x"]
                    sy = s["y"]
                    for enemy in game_map.enemies:
                        ex = enemy.x + enemy.width / 2
                        ey = enemy.y + enemy.height / 2
                        if math.hypot(ex - sx, ey - sy) <= self.strike_radius:
                            enemy.hp -= self.base_damage
                            game_map.damage_texts.append(
                                DamageText(ex, enemy.y, self.base_damage)
                            )
                    s["hit"] = True
                    chain = LightningChain(sx, sy, self.base_damage * 0.6, [])
                    game_map.lightning_chains.append(chain)

        # ----- 빙산: 범위 안 적 1회 데미지 + 얼리기 -----
        elif self.effect_type == "iceberg":
            max_hit_radius = self.size * 1.5
            for enemy in game_map.enemies:
                ex = enemy.x + enemy.width / 2
                ey = enemy.y + enemy.height / 2
                dist = math.hypot(ex - self.x, ey - self.y)
                if dist <= max_hit_radius:
                    if id(enemy) not in self.hit_enemies:
                        enemy.hp -= self.base_damage
                        game_map.damage_texts.append(
                            DamageText(ex, enemy.y, self.base_damage)
                        )
                        enemy.frozen_timer = max(enemy.frozen_timer, self.freeze_time)
                        enemy.ice_hit_count = 0
                        self.hit_enemies.add(id(enemy))

        if self.age >= self.max_lifetime:
            self.active = False

    def draw(self, surface, camera):
        if not self.active:
            return
        cx, cy = camera.apply_pos(self.x, self.y)

        if self.effect_type == "meteor":
            impact_t = self.impact_frame
            total_t = self.max_lifetime
            start_pos = self.extra.get("start_pos", (self.x, self.y - 300))
            sx, sy = camera.apply_pos(start_pos[0], start_pos[1] - 300)


            if self.age <= impact_t:
                flight_t = self.age / impact_t
                mx = sx + (cx - sx) * flight_t
                my = sy + (cy - sy) * flight_t
                pygame.draw.circle(surface, (255, 180, 0), (int(mx), int(my)), 14)
                pygame.draw.circle(surface, (255, 80, 0), (int(mx), int(my)), 10)
                for _ in range(5):
                    off = random.randint(-8, 8)
                    pygame.draw.line(
                        surface, (255, 120, 0),
                        (int(mx + off), int(my + off)),
                        (int(mx), int(my + 25)), 2
                    )

            # 내가짠거 - 1차 메테오
            # if self.age >= impact_t:
            #     explosion_t = (self.age - impact_t) / max(1, (total_t - impact_t))
            #     explosion_t = max(0.0, min(1.0, explosion_t))
            #     explosion_r = int(self.size * (0.5 + 0.5 * explosion_t))
            #     alpha = int(220 * (1 - explosion_t))
            #     expl_surf = pygame.Surface(
            #         (explosion_r * 2, explosion_r * 2), pygame.SRCALPHA
            #     )
            #     pygame.draw.circle(
            #         expl_surf, (255, 120, 0, alpha),
            #         (explosion_r, explosion_r), explosion_r
            #     )
            #     pygame.draw.circle(
            #         expl_surf, (255, 220, 0, alpha),
            #         (explosion_r, explosion_r), int(explosion_r * 0.7)
            #     )
            #     surface.blit(expl_surf, (cx - explosion_r, cy - explosion_r))

            # 이후 Meteor는 GPT
            if self.age >= impact_t:
                phase = (self.age - impact_t) / max(1, (total_t - impact_t))
                phase = max(0.0, min(1.0, phase))
                base_radius = self.size
                main_r = int(base_radius * (0.7 + 0.6 * phase))
                inner_r = int(main_r * 0.55)
                core_r = int(main_r * 0.3)
                smoke_r = int(main_r * 1.3)
                expl_surf = pygame.Surface((main_r * 2, main_r * 2), pygame.SRCALPHA)
                center = (main_r, main_r)

                smoke_alpha = int(180 * (1 - phase))
                if smoke_alpha > 0:
                    pygame.draw.circle(expl_surf, (40, 40, 40, smoke_alpha), center, smoke_r)
                outer_alpha = int(230 * (1 - phase * 0.7))
                if outer_alpha > 0:
                    pygame.draw.circle(expl_surf, (255, 120, 0, outer_alpha), center, main_r)
                mid_alpha = int(240 * (1 - phase * 0.8))
                if mid_alpha > 0:
                    pygame.draw.circle(expl_surf, (255, 220, 0, mid_alpha), center, inner_r)
                core_alpha = int(255 * (1 - phase))
                if core_alpha > 0:
                    pygame.draw.circle(expl_surf, (255, 255, 255, core_alpha), center, core_r)

                surface.blit(expl_surf, (cx - main_r, cy - main_r))

                wave_r = int(base_radius * (0.4 + phase * 1.5))
                wave_alpha = int(220 * (1 - phase))
                if wave_alpha > 0 and wave_r > 0:
                    ring_surf = pygame.Surface((wave_r * 2, wave_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surf, (255, 230, 200, wave_alpha), (wave_r, wave_r), wave_r, width=4)
                    pygame.draw.circle(ring_surf, (255, 255, 255, min(255, wave_alpha + 20)), (wave_r, wave_r), int(wave_r * 0.85), width=2)
                    surface.blit(ring_surf, (cx - wave_r, cy - wave_r))

                num_sparks = 26
                for _ in range(num_sparks):
                    ang = random.uniform(0, math.tau)
                    dist = random.uniform(base_radius * 0.3, base_radius * (0.6 + phase * 1.2))
                    px = cx + math.cos(ang) * dist
                    py = cy + math.sin(ang) * dist
                    size = random.randint(2, 4)
                    spark_alpha = int(255 * (1 - phase))
                    if spark_alpha <= 0:
                        continue
                    pygame.draw.circle(surface, (255, 200, 120, spark_alpha), (int(px), int(py)), size)
                    pygame.draw.circle(surface, (255, 255, 220, min(255, spark_alpha + 40)), (int(px), int(py)), max(1, size - 1))

                if impact_t <= self.age <= impact_t + 10:
                    scorch_r = int(base_radius * 1.2)
                    scorch_surf = pygame.Surface((scorch_r * 2, scorch_r * 2), pygame.SRCALPHA)
                    pygame.draw.circle(scorch_surf, (20, 10, 5, 140), (scorch_r, scorch_r), scorch_r)
                    pygame.draw.circle(scorch_surf, (60, 35, 15, 110), (scorch_r, scorch_r), int(scorch_r * 0.6))
                    surface.blit(scorch_surf, (cx - scorch_r, cy - scorch_r))

        # ----- 천둥: 1차
        # elif self.effect_type == "thunder":
        #     strike_duration = 25
        #     for s in self.strikes:
        #         if s["start"] <= self.age <= s["start"] + strike_duration:
        #             sx, sy = camera.apply_pos(s["x"], s["y"])
        #             height = 260
        #             top_y = sy - height // 2
        #             bottom_y = sy + height // 2
        #             points = []
        #             segs = 25
        #             for i in range(segs + 1):
        #                 ty = top_y + (bottom_y - top_y) * i / segs
        #                 jitter = random.randint(-8, 8)
        #                 points.append((sx + jitter, ty))
        #             pygame.draw.lines(surface, (255, 255, 200), False, points, 4)
        #             pygame.draw.lines(surface, (255, 255, 255), False, points, 2)
        #             wave_r = int(self.strike_radius * (self.age - s["start"]) / strike_duration)
        #             if wave_r > 0:
        #                 pygame.draw.circle(surface, (255, 255, 180), (sx, sy), wave_r, 2)
        #     glow_r = int(self.size * 1.1)
        #     glow_alpha = int(80 + 60 * math.sin(self.age * 0.3))
        #     glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        #     pygame.draw.circle(glow_surf, (255, 255, 200, max(0, glow_alpha)),
        #                        (glow_r, glow_r), glow_r, 3)
        #     surface.blit(glow_surf, (cx - glow_r, cy - glow_r))

        # 이후 번개는 GPT
        elif self.effect_type == "thunder":
            strike_duration = 25
            dark_alpha = int(110 * (0.5 + 0.5 * math.sin(self.age * 0.25)))
            if dark_alpha > 0:
                dark_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                dark_surf.fill((0, 0, 20, dark_alpha))
                surface.blit(dark_surf, (0, 0))

            for s in self.strikes:
                if s["start"] <= self.age <= s["start"] + strike_duration:
                    sx, sy = camera.apply_pos(s["x"], s["y"])
                    height = 300
                    top_y = sy - height // 2
                    bottom_y = sy + height // 2

                    points = []
                    segs = 18
                    for i in range(segs + 1):
                        ty = top_y + (bottom_y - top_y) * i / segs
                        jitter = random.randint(-14, 14)
                        points.append((sx + jitter, ty))
                    if len(points) >= 2:
                        pygame.draw.lines(surface, (255, 255, 140), False, points, 7)
                        pygame.draw.lines(surface, (255, 255, 255), False, points, 3)

                    explosion_r = int(self.strike_radius * (self.age - s["start"]) / strike_duration)
                    if explosion_r > 0:
                        boom_alpha = int(180 * (1 - (explosion_r / max(1, self.strike_radius * 1.4))))
                        boom_surf = pygame.Surface((explosion_r * 2, explosion_r * 2), pygame.SRCALPHA)
                        pygame.draw.circle(boom_surf, (255, 240, 150, boom_alpha), (explosion_r, explosion_r), explosion_r)
                        pygame.draw.circle(boom_surf, (255, 255, 255, int(boom_alpha * 0.7)), (explosion_r, explosion_r), int(explosion_r * 0.6))
                        surface.blit(boom_surf, (sx - explosion_r, sy - explosion_r))

                    for _ in range(8):
                        ang = random.uniform(0, math.tau)
                        dist = random.uniform(10, 40)
                        px = sx + math.cos(ang) * dist
                        py = sy + math.sin(ang) * dist
                        pygame.draw.line(surface, (255, 255, 180), (sx, sy), (int(px), int(py)), 1)

            glow_r = int(self.size * 1.4)
            glow_alpha = int(90 + 60 * math.sin(self.age * 0.4))
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (200, 240, 255, max(0, glow_alpha)), (glow_r, glow_r), glow_r, 4)
            surface.blit(glow_surf, (cx - glow_r, cy - glow_r))

        # ----- 빙산: 1차 
        # elif self.effect_type == "iceberg":
        #     spike_count = 10
        #     base_r = self.size * 0.3
        #     grow_time = self.max_lifetime * (1/3)
        #     if self.age < grow_time:
        #         spike_progress = self.age / grow_time
        #     else:
        #         spike_progress = 1.0
        #     spike_len = self.size * 0.7 * spike_progress
        #     for i in range(spike_count):
        #         angle = (2 * math.pi / spike_count) * i
        #         bx = cx + math.cos(angle) * base_r
        #         by = cy + math.sin(angle) * base_r
        #         tipx = bx + math.cos(angle) * spike_len
        #         tipy = by + math.sin(angle) * spike_len * 1.1
        #         jitter = math.sin(self.age * 0.2 + i) * 3
        #         tipy += jitter
        #         points = [
        #             (bx - 8 * math.sin(angle), by + 8 * math.cos(angle)),
        #             (bx + 8 * math.sin(angle), by - 8 * math.cos(angle)),
        #             (tipx, tipy),
        #         ]
        #         pygame.draw.polygon(surface, (180, 240, 255), points)
        #         pygame.draw.polygon(surface, (220, 255, 255), points, 1)
        #     pygame.draw.circle(surface, (150, 220, 255), (int(cx), int(cy)),
        #                        int(self.size * 0.25), 2)

        # 이후 빙산 GPT
        elif self.effect_type == "iceberg":
            phase = self.age / self.max_lifetime
            phase = max(0.0, min(1.0, phase))
            base_r = self.size * 0.35
            max_spike_len = self.size * 0.9
            grow_time = self.max_lifetime * (1/3)
            if self.age < grow_time:
                spike_progress = self.age / grow_time
            else:
                spike_progress = 1.0
            spike_len_outer = max_spike_len * spike_progress
            spike_len_inner = spike_len_outer * 0.6

            aura_r = int(self.size * (0.6 + 0.1 * math.sin(self.age * 0.25)))
            aura_alpha = int(140 * (1 - phase * 0.7))
            if aura_alpha > 0:
                aura_surf = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
                center = (aura_r, aura_r)
                pygame.draw.circle(aura_surf, (80, 180, 255, aura_alpha), center, aura_r)
                pygame.draw.circle(aura_surf, (200, 245, 255, int(aura_alpha * 0.8)), center, int(aura_r * 0.65))
                surface.blit(aura_surf, (cx - aura_r, cy - aura_r))

            if phase < 0.6:
                crack_r = self.size * 0.85
                for i in range(7):
                    ang = (math.tau / 7) * i + math.sin(self.age * 0.1) * 0.15
                    length = crack_r * (0.6 + 0.4 * random.random())
                    x1 = cx + math.cos(ang) * 10
                    y1 = cy + math.sin(ang) * 10
                    x2 = cx + math.cos(ang) * length
                    y2 = cy + math.sin(ang) * length
                    pygame.draw.line(surface, (200, 230, 255), (int(x1), int(y1)), (int(x2), int(y2)), 1)

            inner_count = 10
            angle_offset = self.age * 0.05
            for i in range(inner_count):
                angle = (math.tau / inner_count) * i + angle_offset
                bx = cx + math.cos(angle) * (base_r * 0.5)
                by = cy + math.sin(angle) * (base_r * 0.5)
                tipx = bx + math.cos(angle) * spike_len_inner
                tipy = by + math.sin(angle) * spike_len_inner * 1.05
                jitter = math.sin(self.age * 0.3 + i) * 2
                tipx += math.cos(angle + math.pi/2) * jitter
                tipy += math.sin(angle + math.pi/2) * jitter
                points = [
                    (bx - 6 * math.sin(angle), by + 6 * math.cos(angle)),
                    (bx + 6 * math.sin(angle), by - 6 * math.cos(angle)),
                    (tipx, tipy),
                ]
                pygame.draw.polygon(surface, (170, 230, 255), points)
                pygame.draw.polygon(surface, (220, 255, 255), points, 1)

            outer_count = 12
            for i in range(outer_count):
                angle = (math.tau / outer_count) * i - angle_offset * 0.7
                bx = cx + math.cos(angle) * (base_r * 1.0)
                by = cy + math.sin(angle) * (base_r * 1.0)
                tipx = bx + math.cos(angle) * spike_len_outer
                tipy = by + math.sin(angle) * spike_len_outer * 1.1
                swing = math.sin(self.age * 0.2 + i * 0.5) * 4
                tipx += math.cos(angle + math.pi/2) * swing
                tipy += math.sin(angle + math.pi/2) * swing
                points = [
                    (bx - 9 * math.sin(angle), by + 9 * math.cos(angle)),
                    (bx + 9 * math.sin(angle), by - 9 * math.cos(angle)),
                    (tipx, tipy),
                ]
                pygame.draw.polygon(surface, (150, 210, 255), points)
                pygame.draw.polygon(surface, (230, 255, 255), points, 1)

            core_r = int(self.size * 0.3)
            pygame.draw.circle(surface, (160, 220, 255), (int(cx), int(cy)), core_r, 2)
            pygame.draw.circle(surface, (220, 250, 255), (int(cx), int(cy)), int(core_r * 0.55), 1)

            flake_count = 24
            for _ in range(flake_count):
                ang = random.uniform(0, math.tau)
                dist = random.uniform(self.size * 0.1, self.size * 1.4)
                fx = cx + math.cos(ang) * dist
                fy = cy + math.sin(ang) * dist - phase * 10
                size = random.randint(1, 3)
                alpha = int(220 * (1 - phase * 0.9))
                if alpha <= 0:
                    continue
                pygame.draw.circle(surface, (230, 240, 255), (int(fx), int(fy)), size)
                if size >= 2:
                    pygame.draw.circle(surface, (255, 255, 255), (int(fx), int(fy)), size - 1)

        # ----- 역류: 1차
        # elif self.effect_type == "backflow":
        #     origin, direction, half_angle = self.extra
        #     ox, oy = camera.apply_pos(origin[0], origin[1])
        #     if direction == (0, 0):
        #         base_angle = 0.0
        #     else:
        #         base_angle = math.atan2(direction[1], direction[0])
        #     left_angle = base_angle - half_angle
        #     right_angle = base_angle + half_angle
        #     length = self.size * (0.6 + 0.4 * (self.age / self.max_lifetime))
        #     p0 = (ox, oy)
        #     p1 = (ox + math.cos(left_angle) * length, oy + math.sin(left_angle) * length)
        #     p2 = (ox + math.cos(right_angle) * length, oy + math.sin(right_angle) * length)
        #     wave_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        #     pygame.draw.polygon(wave_surf, (0, 120, 255, 110), [p0, p1, p2])
        #     pygame.draw.polygon(wave_surf, (200, 240, 255, 90), [p0, p1, p2])
        #     surface.blit(wave_surf, (0, 0))
        #     for k in range(4):
        #         f = (k + self.age * 0.3) / 6
        #         wf = f * length
        #         px = ox + math.cos(base_angle) * wf
        #         py = oy + math.sin(base_angle) * wf
        #         pygame.draw.circle(surface, (180, 220, 255), (int(px), int(py)), 4)

        # 이후 역류 GPT
        elif self.effect_type == "backflow":
            origin, direction, half_angle = self.extra
            ox, oy = camera.apply_pos(origin[0], origin[1])
            if direction == (0, 0):
                base_angle = 0.0
            else:
                base_angle = math.atan2(direction[1], direction[0])

            t = self.age / self.max_lifetime
            t = max(0.0, min(1.0, t))
            max_len = self.size
            length = max_len * (0.7 + 0.3 * t)
            left_angle = base_angle - half_angle
            right_angle = base_angle + half_angle

            cone_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

            outer_color = (0, 80, 180, 110)
            inner_color = (0, 170, 255, 180)
            p0 = (ox, oy)
            p1 = (ox + math.cos(left_angle) * length, oy + math.sin(left_angle) * length)
            p2 = (ox + math.cos(right_angle) * length, oy + math.sin(right_angle) * length)
            pygame.draw.polygon(cone_surf, outer_color, [p0, p1, p2])

            inner_half_angle = half_angle * 0.55
            il = base_angle - inner_half_angle
            ir = base_angle + inner_half_angle
            inner_len = length * 0.9
            ip1 = (ox + math.cos(il) * inner_len, oy + math.sin(il) * inner_len)
            ip2 = (ox + math.cos(ir) * inner_len, oy + math.sin(ir) * inner_len)
            pygame.draw.polygon(cone_surf, inner_color, [p0, ip1, ip2])

            edge_color = (200, 240, 255, 230)
            pygame.draw.line(cone_surf, edge_color, p0, p1, 4)
            pygame.draw.line(cone_surf, edge_color, p0, p2, 4)

            ring_count = 5
            for i in range(ring_count):
                f = (i + t * 3) / ring_count
                r = length * f
                if r < 15 or r > length:
                    continue
                segs = 20
                for j in range(segs):
                    ang = il + (ir - il) * (j / segs)
                    jitter = math.sin(t * 10 + j * 0.5) * 3
                    px = ox + math.cos(ang) * (r + jitter)
                    py = oy + math.sin(ang) * (r + jitter)
                    alpha = int(150 * (1 - f))
                    pygame.draw.circle(cone_surf, (180, 230, 255, max(0, alpha)), (int(px), int(py)), 2)

            whirl_r = int(24 + 6 * math.sin(self.age * 0.5))
            pygame.draw.circle(cone_surf, (0, 110, 230, 230), (int(ox), int(oy)), whirl_r, 3)
            pygame.draw.circle(cone_surf, (210, 245, 255, 210), (int(ox), int(oy)), int(whirl_r * 0.6), 2)

            drop_count = 18
            for _ in range(drop_count):
                f = random.uniform(0.2, 1.0) * t
                if f <= 0:
                    continue
                r = length * f
                ang = base_angle + random.uniform(-inner_half_angle * 0.8, inner_half_angle * 0.8)
                px = ox + math.cos(ang) * r
                py = oy + math.sin(ang) * r
                size = random.randint(2, 4)
                alpha = int(220 * (1 - f))
                pygame.draw.circle(cone_surf, (180, 230, 255, max(0, alpha)), (int(px), int(py)), size)

            mist_alpha = int(70 * (1 - abs(0.5 - t) * 2))
            if mist_alpha > 0:
                mist = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                mist.fill((0, 40, 70, mist_alpha))
                cone_surf.blit(mist, (0, 0))

            surface.blit(cone_surf, (0, 0))


class Spell:
    def __init__(self, x, y, dx, dy, spell_type="fireball", target_distance=None):
        self.x, self.y, self.dx, self.dy = x, y, dx, dy
        self.spell_type = spell_type
        self.active = True
        self.distance_traveled = 0

        if spell_type == "fireball":
            self.speed = 10
            self.radius = 8
            self.damage = 25
            self.max_distance = 600
            self.color = RED
        elif spell_type == "ice_lans":
            self.speed = 7
            self.radius = 10
            self.damage = 30
            self.max_distance = 550
            self.color = CYAN
        elif spell_type == "lightning_bolt":
            self.speed = 15
            self.radius = 6
            self.damage = 35
            self.max_distance = 650
            self.color = YELLOW
        elif spell_type == "water_blast":
            self.speed = 9
            self.radius = 9
            self.damage = 28
            self.max_distance = 580
            self.color = BLUE
        else:
            self.speed = 10
            self.radius = 8
            self.damage = 25
            self.max_distance = 600
            self.color = RED

        if target_distance is not None:
            self.max_distance = target_distance

    def update(self):
        remaining = self.max_distance - self.distance_traveled
        step = self.speed
        if remaining <= 0:
            self.active = False
            return
        if step >= remaining:
            move = remaining
            self.x += self.dx * move
            self.y += self.dy * move
            self.distance_traveled = self.max_distance
            self.active = False
        else:
            self.x += self.dx * step
            self.y += self.dy * step
            self.distance_traveled += step

    def draw(self, surface, camera):
        if self.spell_type == "fireball":
            self.draw_fireball(surface, camera)
        elif self.spell_type == "ice_lans":
            self.draw_ice(surface, camera)
        elif self.spell_type == "lightning_bolt":
            self.draw_lightning(surface, camera)
        elif self.spell_type == "water_blast":
            self.draw_water(surface, camera)
        else:
            sx, sy = camera.apply_pos(self.x, self.y)
            pygame.draw.circle(surface, self.color, (int(sx), int(sy)), self.radius)

    def draw_fireball(self, surface, camera):
        sx, sy = camera.apply_pos(self.x, self.y)
        tail_length = 20
        tx = sx - self.dx * tail_length
        ty = sy - self.dy * tail_length
        for i in range(3):
            off = random.randint(-2, 2)
            pygame.draw.line(surface, (255, 120 + 40 * i // 2, 0), (int(tx + off), int(ty + off)), (int(sx), int(sy)), 2)
        pygame.draw.circle(surface, (255, 80, 0), (int(sx), int(sy)), self.radius + 3)
        pygame.draw.circle(surface, (220, 0, 0), (int(sx), int(sy)), self.radius)
        pygame.draw.circle(surface, (255, 220, 0), (int(sx), int(sy)), max(1, self.radius - 3))

    def draw_ice(self, surface, camera):
        sx, sy = camera.apply_pos(self.x, self.y)
        pygame.draw.circle(surface, (120, 220, 255), (int(sx), int(sy)), self.radius + 4)
        pygame.draw.circle(surface, (180, 240, 255), (int(sx), int(sy)), self.radius + 1)
        pygame.draw.circle(surface, (200, 255, 255), (int(sx), int(sy)), max(1, self.radius - 3))
        arm_len = self.radius + 4
        pygame.draw.line(surface, WHITE, (int(sx - arm_len), int(sy)), (int(sx + arm_len), int(sy)), 2)
        pygame.draw.line(surface, WHITE, (int(sx), int(sy - arm_len)), (int(sx), int(sy + arm_len)), 2)
        diag = int(arm_len * 0.7)
        pygame.draw.line(surface, WHITE, (int(sx - diag), int(sy - diag)), (int(sx + diag), int(sy + diag)), 1)
        pygame.draw.line(surface, WHITE, (int(sx - diag), int(sy + diag)), (int(sx + diag), int(sy - diag)), 1)

    def draw_lightning(self, surface, camera):
        sx, sy = camera.apply_pos(self.x, self.y)
        start_x, start_y = sx, sy
        total_length = 35
        segments = 5
        seg_len = total_length / segments
        dir_x, dir_y = self.dx, self.dy
        points = [(start_x, start_y)]
        cx, cy = start_x, start_y
        for _ in range(segments):
            cx += dir_x * seg_len
            cy += dir_y * seg_len
            perp_x, perp_y = -dir_y, dir_x
            rand_scale = random.uniform(-5, 5)
            cx2 = cx + perp_x * rand_scale
            cy2 = cy + perp_y * rand_scale
            points.append((cx2, cy2))
        if len(points) >= 2:
            pygame.draw.lines(surface, (255, 255, 80), False, [(int(px), int(py)) for px, py in points], 3)
            pygame.draw.lines(surface, (255, 255, 255), False, [(int(px), int(py)) for px, py in points], 1)
        pygame.draw.circle(surface, (255, 255, 180), (int(sx), int(sy)), self.radius)

    def draw_water(self, surface, camera):
        sx, sy = camera.apply_pos(self.x, self.y)
        pygame.draw.circle(surface, (0, 120, 255), (int(sx), int(sy)), self.radius + 2)
        pygame.draw.circle(surface, (0, 180, 255), (int(sx), int(sy)), self.radius)
        pygame.draw.circle(surface, (200, 240, 255), (int(sx), int(sy)), max(1, self.radius - 3))
        t = pygame.time.get_ticks() / 200
        wave_r = self.radius + 4 + int(2 * math.sin(t))
        pygame.draw.circle(surface, (180, 220, 255), (int(sx), int(sy)), wave_r, 1)



class BaseEnemy:
    def __init__(self, x, y):
        self.home_x, self.home_y, self.x, self.y = x, y, x, y
        self.state = 'idle'
        self.width, self.height = int(35 * PLAYER_SCALE), int(35 * PLAYER_SCALE)
        self.speed, self.max_hp, self.hp, self.damage = 2.0, 50, 50, 10
        self.attack_cooldown, self.attack_range = 0, 50 * PLAYER_SCALE * 0.8
        self.aggro_radius, self.leash_radius = 300, 500
        self.color = PURPLE
        self.enemy_type = None
        self.is_dummy = False
        self.burn_stacks = []
        self.ice_hit_count = 0
        self.frozen_timer = 0
        self.slow_timer = 0
        self.original_speed = self.speed

    def apply_burn(self, duration=600, total_damage=50):
        damage_per_tick = total_damage / (duration / 30)
        self.burn_stacks.append({
            'remaining': duration,
            'damage_per_tick': damage_per_tick,
            'tick_interval': 30,
            'last_tick': 0
        })

    def apply_ice_hit(self):
        self.ice_hit_count += 1
        if self.ice_hit_count >= 5:
            self.frozen_timer = 180
            self.ice_hit_count = 0

    def apply_slow(self, duration=300):
        self.slow_timer = duration
        self.speed = self.original_speed * 0.3

    def update_status_effects(self, damage_texts=None):
        for burn in self.burn_stacks[:]:
            burn['remaining'] -= 1
            burn['last_tick'] += 1
            if burn['last_tick'] >= burn['tick_interval']:
                self.hp -= burn['damage_per_tick']
                burn['last_tick'] = 0
                if damage_texts is not None:
                    damage_texts.append(DamageText(
                        self.x + self.width / 2,
                        self.y,
                        burn['damage_per_tick']
                    ))
            if burn['remaining'] <= 0:
                self.burn_stacks.remove(burn)

        if self.frozen_timer > 0:
            self.frozen_timer -= 1
        if self.slow_timer > 0:
            self.slow_timer -= 1
            if self.slow_timer == 0:
                self.speed = self.original_speed

    def _move_towards(self, target_x, target_y, game_map):
        if self.frozen_timer > 0:
            return math.hypot(target_x - self.x, target_y - self.y)
        dx, dy = target_x - self.x, target_y - self.y
        dist = math.hypot(dx, dy)
        if dist > self.speed:
            vx, vy = (dx / dist) * self.speed, (dy / dist) * self.speed
            if not game_map or not game_map.rect_blocked(pygame.Rect(self.x + vx, self.y, self.width, self.height)):
                self.x += vx
            if not game_map or not game_map.rect_blocked(pygame.Rect(self.x, self.y + vy, self.width, self.height)):
                self.y += vy
        return dist

    def attack(self, player, projectiles):
        if self.frozen_timer > 0:
            return
        if self.attack_cooldown <= 0 and math.hypot(self.x - player.x, self.y - player.y) < self.attack_range:
            player.hp -= self.damage
            self.attack_cooldown = 60

    def update(self, player, game_map, projectiles, damage_texts=None):
        self.update_status_effects(damage_texts)
        dist_to_player = math.hypot(self.x - player.x, self.y - player.y)
        dist_to_home = math.hypot(self.x - self.home_x, self.y - self.home_y)

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.state == 'waiting' and dist_to_player < self.aggro_radius:
            self.state = 'chasing'
        elif self.state == 'chasing':
            if dist_to_home > self.leash_radius or dist_to_player > self.aggro_radius * 1.2:
                self.state = 'returning'
            else:
                self._move_towards(player.x, player.y, game_map)
                self.attack(player, projectiles)
        elif self.state == 'returning':
            if self._move_towards(self.home_x, self.home_y, game_map) < self.speed:
                self.x, self.y, self.hp, self.state = self.home_x, self.home_y, self.max_hp, 'waiting'

    def draw_health_bar(self, surface, sx, sy):
        pygame.draw.rect(surface, DARK_RED, (sx, sy - 10, 40, 5))
        pygame.draw.rect(surface, RED, (sx, sy - 10, 40 * max(0, self.hp / self.max_hp), 5))

    def draw_level_bar(self,surface,sx,sy):
        if not hasattr(self, "level"):
            return
        font = get_korean_font(18)
        text = font.render(f"Lv.{self.level}", True, WHITE)
        rect = text.get_rect(midbottom=(sx + self.width // 2, sy - 2))
        surface.blit(text, rect)

    def draw_status_effects(self, surface, sx, sy):
        if self.burn_stacks:
            for _ in range(2):
                flame_x = sx + self.width / 2 + random.randint(-10, 10)
                flame_y = sy + random.randint(0, self.height)
                flame_size = random.randint(3, 6)
                pygame.draw.circle(surface, (255, 100, 0), (int(flame_x), int(flame_y)), flame_size)
                pygame.draw.circle(surface, (255, 200, 0), (int(flame_x), int(flame_y)), max(1, flame_size - 2))

        if self.frozen_timer > 0:
            ice_surf = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
            ice_color = (150, 220, 255, 150)
            pygame.draw.rect(ice_surf, ice_color, (0, 0, self.width + 10, self.height + 10), 0)
            for i in range(3):
                pygame.draw.rect(ice_surf, (200, 240, 255, 100), (i, i, self.width + 10 - i*2, self.height + 10 - i*2), 1)
            surface.blit(ice_surf, (sx - 5, sy - 5))
            cx = sx + self.width / 2
            cy = sy + self.height / 2
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                x1 = cx + math.cos(rad) * 5
                y1 = cy + math.sin(rad) * 5
                x2 = cx + math.cos(rad) * 15
                y2 = cy + math.sin(rad) * 15
                pygame.draw.line(surface, (200, 240, 255), (int(x1), int(y1)), (int(x2), int(y2)), 2)

        if self.slow_timer > 0:
            for _ in range(3):
                drop_x = sx + self.width / 2 + random.randint(-15, 15)
                drop_y = sy + random.randint(-5, self.height)
                drop_size = random.randint(2, 4)
                pygame.draw.circle(surface, (100, 150, 255), (int(drop_x), int(drop_y)), drop_size)
                pygame.draw.circle(surface, (150, 200, 255), (int(drop_x), int(drop_y - 1)), max(1, drop_size - 1))

    def draw(self, surface, camera):
        sx, sy = camera.apply(self)
        draw_color = ORANGE if self.state == 'chasing' else CYAN if self.state == 'returning' else self.color
        pygame.draw.rect(surface, draw_color, (sx, sy, self.width, self.height))
        self.draw_health_bar(surface, sx, sy)
        self.draw_level_bar(surface, sx, sy)
        self.draw_status_effects(surface, sx, sy)


# ============================================================================
# Dummy 클래스 - GPT
# ============================================================================
class Dummy(BaseEnemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        base_w = 40 * PLAYER_SCALE
        base_h = 60 * PLAYER_SCALE
        self.scale = DUMMY_SCALE
        self.width = int(base_w * self.scale)
        self.height = int(base_h * self.scale)
        self.max_hp = 9999
        self.hp = self.max_hp
        self.damage = 0
        self.speed = 0
        self.color = (210, 180, 140)
        self.enemy_type = "dummy"
        self.is_dummy = True
        self.aggro_radius = 0
        self.leash_radius = 0
        self.hp_regen_rate = 20
        self.hp_regen_counter = 0

    def update(self, player, game_map, projectiles, damage_texts=None):
        self.update_status_effects(damage_texts)
        self.hp_regen_counter += 1
        if self.hp_regen_counter >= 3:
            self.hp = min(self.max_hp, self.hp + self.hp_regen_rate)
            self.hp_regen_counter = 0
        if self.hp < 1:
            self.hp = 1

    def attack(self, player, projectiles):
        pass

    def draw(self, surface, camera):
        sx, sy = camera.apply(self)
        w, h = self.width, self.height
        body_color = (139, 90, 43)
        head_color = (238, 203, 173)
        arm_color = (160, 120, 80)

        body_w = w * 0.4
        body_h = h * 0.65
        body_x = sx + (w - body_w) / 2
        body_y = sy + h - body_h
        pygame.draw.rect(surface, body_color, (body_x, body_y, body_w, body_h))

        head_r = int(min(w, h) * 0.22)
        head_cx = sx + w / 2
        head_cy = sy + head_r + h * 0.05
        pygame.draw.circle(surface, head_color, (int(head_cx), int(head_cy)), head_r)

        arm_h = h * 0.12
        arm_y = body_y + arm_h
        pygame.draw.rect(surface, arm_color, (sx, int(arm_y), w, int(arm_h * 0.4)))

        eye_r = max(2, int(head_r * 0.18))
        eye_off_x = head_r * 0.4
        eye_off_y = head_r * 0.2
        pygame.draw.circle(surface, BLACK, (int(head_cx - eye_off_x), int(head_cy - eye_off_y)), eye_r)
        pygame.draw.circle(surface, BLACK, (int(head_cx + eye_off_x), int(head_cy - eye_off_y)), eye_r)

        mouth_y1 = head_cy + head_r * 0.2
        mouth_y2 = mouth_y1 + head_r * 0.25
        line_w = max(1, int(head_r * 0.1))
        pygame.draw.line(surface, BLACK, (int(head_cx - head_r * 0.3), int(mouth_y1)), (int(head_cx + head_r * 0.3), int(mouth_y2)), line_w)
        pygame.draw.line(surface, BLACK, (int(head_cx + head_r * 0.3), int(mouth_y1)), (int(head_cx - head_r * 0.3), int(mouth_y2)), line_w)

        bar_w = w
        bar_h = max(5, int(h * 0.07))
        bar_x = sx
        bar_y = sy - bar_h - 4
        pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_w * max(0, self.hp / self.max_hp), bar_h))

        self.draw_status_effects(surface, sx, sy)

        font_size = int(14 * self.scale)
        font = get_korean_font(font_size)
        label = font.render("훈련용", True, (100, 100, 100))
        label_rect = label.get_rect(center=(sx + w / 2, sy + h + font.get_height()))
        surface.blit(label, label_rect)



class Slime(BaseEnemy):
    def __init__(self, x, y, level=1):
        super().__init__(x, y)
        self.level = max(1, int(level))
        self.width = int(30 * PLAYER_SCALE)
        self.height = int(30 * PLAYER_SCALE)

        base_hp = 30
        hp_per_level = 15
        base_damage = 5
        damage_per_level = 2
        self.max_hp = base_hp + hp_per_level * (self.level - 1)
        self.hp = self.max_hp
        self.damage = base_damage + damage_per_level * (self.level - 1)
        self.speed = 1.5
        self.color = GREEN
        self.enemy_type = "slime"
        self.original_speed = self.speed
        self.stand_frame_index = 0
        self.stand_last_change_time = pygame.time.get_ticks()
        self.dying = False
        self.death_frame_index = 0
        self.death_last_change_time = pygame.time.get_ticks()
        self.death_finished = False

    def update(self, player, game_map, projectiles, damage_texts=None):
        now = pygame.time.get_ticks()
        if self.dying:
            if SLIME_DIE_FRAMES and len(SLIME_DIE_FRAMES) == len(SLIME_DIE_DELAYS):
                delay = SLIME_DIE_DELAYS[self.death_frame_index]
                if now - self.death_last_change_time >= delay:
                    self.death_last_change_time = now
                    self.death_frame_index += 1
                    if self.death_frame_index >= len(SLIME_DIE_FRAMES):
                        self.death_finished = True
            else:
                self.death_finished = True
            return

        self.update_status_effects(damage_texts)
        dist_to_player = math.hypot(self.x - player.x, self.y - player.y)
        dist_to_home = math.hypot(self.x - self.home_x, self.y - self.home_y)

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.state == 'waiting' and dist_to_player < self.aggro_radius:
            self.state = 'chasing'
        elif self.state == 'chasing':
            if dist_to_home > self.leash_radius or dist_to_player > self.aggro_radius * 1.2:
                self.state = 'returning'
            else:
                self._move_towards(player.x, player.y, game_map)
                self.attack(player, projectiles)
        elif self.state == 'returning':
            if self._move_towards(self.home_x, self.home_y, game_map) < self.speed:
                self.x, self.y, self.hp, self.state = self.home_x, self.home_y, self.max_hp, 'waiting'

        if self.hp <= 0 and not self.dying:
            self.dying = True
            self.death_frame_index = 0
            self.death_last_change_time = now
            return

        if SLIME_STAND_FRAMES and len(SLIME_STAND_FRAMES) == len(SLIME_STAND_DELAYS):
            delay = SLIME_STAND_DELAYS[self.stand_frame_index]
            if now - self.stand_last_change_time >= delay:
                self.stand_last_change_time = now
                self.stand_frame_index = (self.stand_frame_index + 1) % len(SLIME_STAND_FRAMES)

    def draw(self, surface, camera):
        sx, sy = camera.apply(self)
        if self.dying and SLIME_DIE_FRAMES:
            idx = min(self.death_frame_index, len(SLIME_DIE_FRAMES) - 1)
            img = SLIME_DIE_FRAMES[idx]
            rect = img.get_rect()
            rect.topleft = (sx, sy)
            surface.blit(img, rect)

        elif (not self.dying) and SLIME_STAND_FRAMES:
            idx = self.stand_frame_index % len(SLIME_STAND_FRAMES)
            img = SLIME_STAND_FRAMES[idx]
            rect = img.get_rect()
            rect.topleft = (sx, sy)
            surface.blit(img, rect)
        else:
            draw_color = (100, 255, 100) if self.state == 'chasing' else (0, 150, 150) if self.state == 'returning' else self.color
            pygame.draw.circle(surface, draw_color, (sx + self.width // 2, sy + self.height // 2), self.width // 2)
        self.draw_health_bar(surface, sx, sy)
        self.draw_status_effects(surface, sx, sy)


class EnemyProjectile:
    def __init__(self, x, y, dx, dy):
        self.x, self.y, self.dx, self.dy = x, y, dx, dy
        self.speed, self.radius, self.damage, self.active = 8, 5, 8, True
        self.distance_traveled, self.max_distance, self.color = 0, 500, DARK_GRAY

    def update(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.distance_traveled += self.speed
        if self.distance_traveled > self.max_distance:
            self.active = False

    def draw(self, surface, camera):
        sx, sy = camera.apply_pos(self.x, self.y)
        pygame.draw.circle(surface, self.color, (int(sx), int(sy)), self.radius)


#GPT한테 이름 추천받음
SPELL_DISPLAY_NAMES = {
    "fireball": "파이어볼",
    "ice_lans": "아이스 랜스",
    "lightning_bolt": "라이트닝 볼트",
    "water_blast": "워터 블라스트",
    "meteor": "메테오",
    "thunder": "천둥",
    "iceberg": "빙산",
    "backflow": "역류",
}

SPELLBOOK_ITEMS = {
    "불 마법서 (C랭크)": ("fireball", "C"),
    "얼음 마법서 (C랭크)": ("ice_lans", "C"),
    "번개 마법서 (C랭크)": ("lightning_bolt", "C"),
    "물 마법서 (C랭크)": ("water_blast", "C"),
    "불 마법서 (S랭크)": ("meteor", "S"),
    "번개 마법서 (S랭크)": ("thunder", "S"),
    "얼음 마법서 (S랭크)": ("iceberg", "S"),
    "물 마법서 (S랭크)": ("backflow", "S"),
}

WEAPON_ITEMS = {
    "초급 지팡이": "초급 지팡이",
    "중급 지팡이": "중급 지팡이",
    "상급 지팡이": "상급 지팡이",
    "마나 지팡이": "마나 지팡이",
}

MAX_SPELL_SLOTS = 4

SLIME_SPELLBOOK_DROPS = [
    ("불 마법서 (C랭크)", 50),
    ("얼음 마법서 (C랭크)", 30),
    ("번개 마법서 (C랭크)", 15),
    ("물 마법서 (C랭크)", 5),
]


class ItemDrop:
    def __init__(self, x, y, item_name):
        self.x = x
        self.y = y
        self.item_name = item_name
        self.radius = 18

    def get_rect(self):
        return pygame.Rect(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )

    def draw(self, surface, camera):
        sx, sy = camera.apply_pos(self.x, self.y)
        if self.item_name in SPELLBOOK_ITEMS and BOOK_IMAGE is not None:
            rect = BOOK_IMAGE.get_rect(center=(int(sx), int(sy)))
            surface.blit(BOOK_IMAGE, rect)
        else:
            pygame.draw.circle(surface, ORANGE, (int(sx), int(sy)), self.radius)
            pygame.draw.circle(surface, YELLOW, (int(sx), int(sy)), self.radius - 4)
            font = get_korean_font(16)
            short_name = self.item_name[0]
            text = font.render(short_name, True, BLACK)
            text_rect = text.get_rect(center=(int(sx), int(sy)))
            surface.blit(text, text_rect)



class XPOrb:
    def __init__(self, x, y, value=10):
        self.x = x
        self.y = y
        self.value = value
        self.radius = 10
        self.speed = 4.0

    def update(self, player):
        px = player.x + player.width / 2
        py = player.y + player.height / 2
        dx = px - self.x
        dy = py - self.y
        dist = math.hypot(dx, dy)
        if dist > 1:
            vx = dx / dist * self.speed
            vy = dy / dist * self.speed
            self.x += vx
            self.y += vy

    def draw(self, surface, camera):
        sx, sy = camera.apply_pos(self.x, self.y)
        pygame.draw.circle(surface, (0, 150, 0), (int(sx), int(sy)), self.radius)
        pygame.draw.circle(surface, (0, 220, 0), (int(sx), int(sy)), self.radius - 3)
        pygame.draw.circle(surface, (200, 255, 200), (int(sx), int(sy)), max(1, self.radius - 6))






class GameMap:
    def __init__(self, map_name, tiled_map):
        self.name = map_name
        self.tiled_map = tiled_map
        self.enemies = []
        self.enemies_spawned = False
        self.portals = self.tiled_map.find_portals()
        self.respawn_queue = []
        self.lightning_chains = []
        self.damage_texts = []
        self.area_effects = []
        print(f"[DEBUG] GameMap '{self.name}' 포탈 수: {len(self.portals)}")


class Button:
    def __init__(self, x, y, w, h, text, color, hover_color):
        self.rect, self.text, self.color, self.hover_color = pygame.Rect(x, y, w, h), text, color, hover_color
        self.is_hovered = False

    def draw(self, surface):
        pygame.draw.rect(surface, self.hover_color if self.is_hovered else self.color, self.rect)
        pygame.draw.rect(surface, WHITE, self.rect, 3)
        text_surf = get_korean_font(36).render(self.text, True, WHITE)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, pos, pressed):
        return self.rect.collidepoint(pos) and pressed[0]


def draw_target_marker(surface, camera, world_x, world_y):
    sx, sy = camera.apply_pos(world_x, world_y)
    pulse = int(10 + 5 * math.sin(pygame.time.get_ticks() / 300))
    pygame.draw.line(surface, CYAN, (sx - pulse, sy), (sx + pulse, sy), 2)
    pygame.draw.line(surface, CYAN, (sx, sy - pulse), (sx, sy + pulse), 2)
    pygame.draw.circle(surface, CYAN, (sx, sy), 15, 2)


def character_selection():
    male_btn = Button(300, 600, 400, 160, "남자", BLUE, (0, 150, 255))
    female_btn = Button(900, 600, 400, 160, "여자", (255, 105, 180), (255, 150, 200))
    while True:
        pos, pressed = pygame.mouse.get_pos(), pygame.mouse.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        male_btn.check_hover(pos)
        female_btn.check_hover(pos)
        if male_btn.is_clicked(pos, pressed):
            return 'male'
        if female_btn.is_clicked(pos, pressed):
            return 'female'
        screen.fill(BLACK)
        title_surf = get_korean_font(60).render("캐릭터 선택", True, WHITE)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 150)))
        male_btn.draw(screen)
        female_btn.draw(screen)
        pygame.display.flip()
        clock.tick(60)


# ============================================================================
# UI 관련 함수들 - GPT 활용(draw ui까지)
# ============================================================================
def draw_rounded_bar(surface, x, y, w, h, ratio, back_color, fill_color, border_color):
    ratio = max(0.0, min(1.0, ratio))
    base_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, back_color, base_rect, border_radius=12)
    inner_margin = 3
    inner_w = int((w - inner_margin * 2) * ratio)
    if inner_w > 0:
        inner_rect = pygame.Rect(x + inner_margin, y + inner_margin, inner_w, h - inner_margin * 2)
        pygame.draw.rect(surface, fill_color, inner_rect, border_radius=10)
    pygame.draw.rect(surface, border_color, base_rect, width=2, border_radius=12)

def draw_ui(surface, player, current_map, target_set):

    big_font = get_korean_font(26)
    font = get_korean_font(18)

    bar_x = 20
    bar_y = 20
    bar_w = 300
    bar_h = 40
    gap = 10

    hp_ratio = player.hp / player.max_hp if player.max_hp > 0 else 0
    draw_rounded_bar(surface, bar_x, bar_y, bar_w, bar_h, hp_ratio, DARK_GRAY, RED, (60, 0, 0))
    hp_text = font.render(f"HP {int(player.hp)}/{player.max_hp}", True, WHITE)
    hp_text_rect = hp_text.get_rect(center=(bar_x + bar_w // 2, bar_y + bar_h // 2))
    surface.blit(hp_text, hp_text_rect)

    mp_y = bar_y + bar_h + gap
    mp_ratio = player.mp / player.max_mp if player.max_mp > 0 else 0
    draw_rounded_bar(surface, bar_x, mp_y, bar_w, bar_h, mp_ratio, DARK_GRAY, BLUE, (0, 0, 80))
    mp_text = font.render(f"MP {int(player.mp)}/{player.max_mp}", True, WHITE)
    mp_text_rect = mp_text.get_rect(center=(bar_x + bar_w // 2, mp_y + bar_h // 2))
    surface.blit(mp_text, mp_text_rect)

    exp_y = mp_y + bar_h + gap
    if player.xp_to_next > 0:
        exp_ratio = player.xp / player.xp_to_next
    else:
        exp_ratio = 0
    draw_rounded_bar(surface, bar_x, exp_y, bar_w, bar_h, exp_ratio, DARK_GRAY, GREEN, (0, 60, 0))
    exp_text = font.render(f"EXP {int(player.xp)}/{player.xp_to_next}", True, WHITE)
    exp_text_rect = exp_text.get_rect(center=(bar_x + bar_w // 2, exp_y + bar_h // 2))
    surface.blit(exp_text, exp_text_rect)

    lvl_x = bar_x + bar_w + 25
    lvl_y = bar_y
    badge_w = 90
    badge_h = 60
    badge_rect = pygame.Rect(lvl_x, lvl_y, badge_w, badge_h)
    pygame.draw.rect(surface, DARK_GRAY, badge_rect, border_radius=14)
    pygame.draw.rect(surface, YELLOW, badge_rect, width=2, border_radius=14)
    lvl_label = font.render("LEVEL", True, LIGHT_GRAY)
    lvl_value = big_font.render(str(player.level), True, YELLOW)
    lvl_label_rect = lvl_label.get_rect(center=(lvl_x + badge_w // 2, lvl_y + badge_h // 3))
    lvl_value_rect = lvl_value.get_rect(center=(lvl_x + badge_w // 2, lvl_y + badge_h * 2 // 3 + 2))
    surface.blit(lvl_label, lvl_label_rect)
    surface.blit(lvl_value, lvl_value_rect)

    info_font = get_korean_font(18)
    rx = WIDTH - 260
    ry = 24
    if current_map:
        enemies_text = info_font.render(f"적 수: {len(current_map.enemies)}", True, WHITE)
        surface.blit(enemies_text, (rx, ry))
        ry += 24
    pos_text = info_font.render(f"위치: ({int(player.x)}, {int(player.y)})", True, WHITE)
    surface.blit(pos_text, (rx, ry))

    status_text, status_color = (
        ("타겟 설정됨 - Enter: 시전", CYAN) if target_set else ("마우스로 적/위치 지정", GRAY)
    )
    status_surf = info_font.render(status_text, True, status_color)
    surface.blit(status_surf, (bar_x, exp_y + bar_h + 14))
    weapon_text = info_font.render(f"무기: {player.weapon}", True, WHITE)
    surface.blit(weapon_text, (bar_x, exp_y + bar_h + 38))


def draw_inventory(surface, player):
    inv_w, inv_h = 600, 400
    inv_x = (WIDTH - inv_w) // 2
    inv_y = (HEIGHT - inv_h) // 2
    inv_surf = pygame.Surface((inv_w, inv_h))
    inv_surf.set_alpha(200)
    inv_surf.fill(DARK_GRAY)
    pygame.draw.rect(inv_surf, WHITE, (0, 0, inv_w, inv_h), 3)

    title_font = get_korean_font(36)
    item_font = get_korean_font(25)
    title_surf = title_font.render("인벤토리 (I: 닫기, 1~9: 사용)", True, WHITE)
    inv_surf.blit(title_surf, title_surf.get_rect(center=(inv_w // 2, 40)))

    start_y = 90
    line_height = 35
    if not player.inventory:
        empty_surf = item_font.render("인벤토리가 비어 있습니다.", True, LIGHT_GRAY)
        inv_surf.blit(empty_surf, empty_surf.get_rect(center=(inv_w // 2, inv_h // 2)))
    else:
        for idx, (item_name, count) in enumerate(player.inventory.items()):
            label = f"{idx+1}. {item_name} x{count}"
            text_surf = item_font.render(label, True, WHITE)
            inv_surf.blit(text_surf, (40, start_y + idx * line_height))
    surface.blit(inv_surf, (inv_x, inv_y))


def draw_setting(surface, volume):
    set_w, set_h = 1000, 600
    set_x = (WIDTH - set_w) // 2
    set_y = (HEIGHT - set_h) // 2
    set_surf = pygame.Surface((set_w, set_h))
    set_surf.set_alpha(220)
    set_surf.fill(DARK_GRAY)
    pygame.draw.rect(set_surf, WHITE, (0, 0, set_w, set_h), 3)

    title_font = get_korean_font(54)
    item_font = get_korean_font(32)
    small_font = get_korean_font(20)

    title_surf = title_font.render("설정 (ESC: 닫기)", True, WHITE)
    set_surf.blit(title_surf, title_surf.get_rect(center=(set_w // 2, 60)))

    info_lines = [
        "마우스로 슬라이더를 드래그해서 전체 볼륨 조절",
        "녹음 시작/종료: R",
        "마법 시전: 스페이스/마우스 왼쪽",
        "인벤토리: I, 무기 & 마법 선택: E",
    ]
    for idx, line in enumerate(info_lines):
        text_surf = small_font.render(line, True, WHITE)
        set_surf.blit(text_surf, (40, 130 + idx * 28))


    slider_x = 60
    slider_y = 260
    slider_w = 700
    slider_h = 24


    pygame.draw.rect(
        set_surf,
        DARK_GRAY,
        (slider_x, slider_y, slider_w, slider_h),
        border_radius=12
    )


    ratio = max(0.0, min(1.0, volume))
    fill_w = int(slider_w * ratio)
    if fill_w > 0:
        pygame.draw.rect(
            set_surf,
            GREEN,
            (slider_x, slider_y, fill_w, slider_h),
            border_radius=12
        )

 
    pygame.draw.rect(
        set_surf,
        WHITE,
        (slider_x, slider_y, slider_w, slider_h),
        width=2,
        border_radius=12
    )


    handle_x = slider_x + fill_w
    handle_y = slider_y + slider_h // 2
    pygame.draw.circle(set_surf, WHITE, (handle_x, handle_y), slider_h // 2 + 4)
    pygame.draw.circle(set_surf, GREEN, (handle_x, handle_y), slider_h // 2)


    vol_text = item_font.render(f"전체 볼륨: {int(ratio * 100)}%", True, WHITE)
    set_surf.blit(vol_text, (slider_x, slider_y - 40))

    hint = small_font.render("※ 슬라이더를 클릭/드래그해서 조절하세요.", True, LIGHT_GRAY)
    set_surf.blit(hint, (slider_x, slider_y + slider_h + 20))

    surface.blit(set_surf, (set_x, set_y))


    return pygame.Rect(set_x + slider_x, set_y + slider_y, slider_w, slider_h)

def draw_swap_menu(surface, player, swap_phase, swap_selected_slot, swap_selected_index, swap_unequipped_spells):
    title_font = get_korean_font(34)
    item_font = get_korean_font(24)
    small_font = get_korean_font(18)

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(230)
    overlay.fill(DARK_GRAY)

    title = title_font.render("마법 교체 (M)", True, WHITE)
    overlay.blit(title, title.get_rect(center=(WIDTH//2, 90)))

    if swap_phase == 0:
        info1 = small_font.render("1단계: 교체할 슬롯 선택", True, YELLOW)
        info2 = small_font.render("↑↓/WS 또는 1~4 선택", True, WHITE)
        info3 = small_font.render("Enter/Space: 다음 단계", True, LIGHT_GRAY)
    else:
        info1 = small_font.render("2단계: 장착할 마법 선택", True, YELLOW)
        info2 = small_font.render("↑↓/WS", True, WHITE)
        info3 = small_font.render("Enter/Space: 장착", True, LIGHT_GRAY)

    overlay.blit(info1, (WIDTH//2 - 260, 130))
    overlay.blit(info2, (WIDTH//2 - 260, 160))
    overlay.blit(info3, (WIDTH//2 - 260, 190))

    left_x = WIDTH//2 - 320
    start_y = 240
    line_h = 40
    slot_title = item_font.render("슬롯 (장착 중)", True, WHITE)
    overlay.blit(slot_title, (left_x, start_y - 40))

    for i in range(MAX_SPELL_SLOTS):
        if i < len(player.equipped_spells):
            spl = player.equipped_spells[i]
            name = SPELL_DISPLAY_NAMES.get(spl, spl)
            rank = player.known_spells.get(spl, "?")
            label = f"{i+1}. {name} ({rank}랭크)"
        else:
            label = f"{i+1}. - 비어 있음 -"

        if i == swap_selected_slot:
            color = YELLOW if swap_phase == 0 else CYAN
            prefix = "▶ "
        else:
            color = WHITE
            prefix = "  "

        text = item_font.render(prefix + label, True, color)
        overlay.blit(text, (left_x, start_y + i * line_h))

    right_x = WIDTH//2 + 40
    spell_title = item_font.render("장착 가능 마법 (미장착)", True, WHITE)
    overlay.blit(spell_title, (right_x, start_y - 40))

    for idx, sid in enumerate(swap_unequipped_spells):
        name = SPELL_DISPLAY_NAMES.get(sid, sid)
        rank = player.known_spells.get(sid, "?")
        label = f"{name} ({rank}랭크)"

        if swap_phase == 1 and idx == swap_selected_index:
            color = YELLOW
            prefix = "▶ "
        else:
            color = WHITE
            prefix = "  "

        text = item_font.render(prefix + label, True, color)
        overlay.blit(text, (right_x, start_y + idx * line_h))

    esc_text = small_font.render("ESC: 취소", True, LIGHT_GRAY)
    overlay.blit(esc_text, (WIDTH//2 - 40, HEIGHT - 80))

    surface.blit(overlay, (0, 0))

def swap_skills(player, selected_slot):
    spells = list(player.known_spells.keys())
    equipped_set = set(player.equipped_spells[:MAX_SPELL_SLOTS])
    unequipped_spells = [sid for sid in spells if sid not in equipped_set]

    if not unequipped_spells:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(BLACK)
        font = get_korean_font(32)
        small = get_korean_font(20)
        t1 = font.render("장착되지 않은 마법이 없습니다.", True, WHITE)
        t2 = small.render("새로 끼울 마법이 없습니다.", True, LIGHT_GRAY)
        overlay.blit(t1, t1.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))
        overlay.blit(t2, t2.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))
        screen.blit(overlay, (0,0))
        pygame.display.flip()
        pygame.time.wait(1000)
        return None

    selected_slot = max(0, min(selected_slot, MAX_SPELL_SLOTS - 1))
    selected_index = 0
    phase = 0

    title_font = get_korean_font(34)
    item_font = get_korean_font(24)
    small_font = get_korean_font(18)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None

                if phase == 0:
                    if pygame.K_1 <= event.key <= pygame.K_4:
                        idx = event.key - pygame.K_1
                        if 0 <= idx < MAX_SPELL_SLOTS:
                            selected_slot = idx

                    if event.key in (pygame.K_UP, pygame.K_w):
                        selected_slot = (selected_slot - 1) % MAX_SPELL_SLOTS
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        selected_slot = (selected_slot + 1) % MAX_SPELL_SLOTS

                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        phase = 1

                else:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        selected_index = (selected_index - 1) % len(unequipped_spells)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        selected_index = (selected_index + 1) % len(unequipped_spells)

                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        new_spell = unequipped_spells[selected_index]

                        if selected_slot >= len(player.equipped_spells):
                            if len(player.equipped_spells) < MAX_SPELL_SLOTS:
                                player.equipped_spells.append(new_spell)
                        else:
                            player.equipped_spells[selected_slot] = new_spell

                        return selected_slot

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(230)
        overlay.fill(DARK_GRAY)

        title = title_font.render("마법 교체 (M)", True, WHITE)
        overlay.blit(title, title.get_rect(center=(WIDTH//2, 90)))

        if phase == 0:
            info1 = small_font.render("1단계: 교체할 슬롯 선택", True, YELLOW)
            info2 = small_font.render("↑↓/WS 또는 1~4 선택", True, WHITE)
            info3 = small_font.render("Enter/Space: 다음 단계", True, LIGHT_GRAY)
        else:
            info1 = small_font.render("2단계: 장착할 마법 선택", True, YELLOW)
            info2 = small_font.render("↑↓/WS", True, WHITE)
            info3 = small_font.render("Enter/Space: 장착", True, LIGHT_GRAY)

        overlay.blit(info1, (WIDTH//2 - 260, 130))
        overlay.blit(info2, (WIDTH//2 - 260, 160))
        overlay.blit(info3, (WIDTH//2 - 260, 190))

        left_x = WIDTH//2 - 320
        start_y = 240
        line_h = 40
        slot_title = item_font.render("슬롯 (장착 중)", True, WHITE)
        overlay.blit(slot_title, (left_x, start_y - 40))

        for i in range(MAX_SPELL_SLOTS):
            if i < len(player.equipped_spells[:MAX_SPELL_SLOTS]):
                spl = player.equipped_spells[i]
                name = SPELL_DISPLAY_NAMES.get(spl, spl)
                rank = player.known_spells.get(spl, "?")
                label = f"{i+1}. {name} ({rank}랭크)"
            else:
                label = f"{i+1}. - 비어 있음 -"

            if i == selected_slot:
                color = YELLOW if phase == 0 else CYAN
                prefix = "▶ "
            else:
                color = WHITE
                prefix = "  "

            text = item_font.render(prefix + label, True, color)
            overlay.blit(text, (left_x, start_y + i * line_h))

        right_x = WIDTH//2 + 40
        spell_title = item_font.render("장착 가능 마법 (미장착)", True, WHITE)
        overlay.blit(spell_title, (right_x, start_y - 40))

        for idx, sid in enumerate(unequipped_spells):
            name = SPELL_DISPLAY_NAMES.get(sid, sid)
            rank = player.known_spells.get(sid, "?")
            label = f"{name} ({rank}랭크)"

            if phase == 1 and idx == selected_index:
                color = YELLOW
                prefix = "▶ "
            else:
                color = WHITE
                prefix = "  "

            text = item_font.render(prefix + label, True, color)
            overlay.blit(text, (right_x, start_y + idx * line_h))

        esc_text = small_font.render("ESC: 취소", True, LIGHT_GRAY)
        overlay.blit(esc_text, (WIDTH//2 - 40, HEIGHT - 80))

        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)
   


def use_hp_potion(player):
    if player.inventory.get("HP 포션", 0) > 0:
        heal_amount = 50
        old_hp = player.hp
        player.hp = min(player.max_hp, player.hp + heal_amount)
        player.inventory["HP 포션"] -= 1
        if player.inventory["HP 포션"] <= 0:
            del player.inventory["HP 포션"]
        print(f"HP 포션 사용! {int(old_hp)} -> {int(player.hp)} / {player.max_hp}")
    else:
        print("HP 포션이 없습니다!")


def use_mp_potion(player):
    if player.inventory.get("MP 포션", 0) > 0:
        regen_amount = 50
        old_mp = player.mp
        player.mp = min(player.max_mp, player.mp + regen_amount)
        player.inventory["MP 포션"] -= 1
        if player.inventory["MP 포션"] <= 0:
            del player.inventory["MP 포션"]


ITEM_USE_FUNCTIONS = {
    "HP 포션": use_hp_potion,
    "MP 포션": use_mp_potion,
}


def learn_spell_from_book(player, item_name):
    if player.inventory.get(item_name, 0) <= 0:
        return
    if item_name not in SPELLBOOK_ITEMS:
        return

    spell_id, new_rank = SPELLBOOK_ITEMS[item_name]
    display_name = SPELL_DISPLAY_NAMES.get(spell_id, spell_id)
    prev_rank = player.known_spells.get(spell_id)
    player.known_spells[spell_id] = new_rank

    if spell_id not in player.equipped_spells and len(player.equipped_spells) < MAX_SPELL_SLOTS:
        player.equipped_spells.append(spell_id)

    player.inventory[item_name] -= 1
    if player.inventory[item_name] <= 0:
        del player.inventory[item_name]

    if prev_rank is None:
        sound = open_spell_sound_popup(spell_id, display_name, initial_sound=None, mode="new")
        if sound is not None:
            player.spell_sounds[spell_id] = sound


def equip_weapon(player, item_name):
    if player.inventory.get(item_name, 0) <= 0:
        return
    weapon_id = WEAPON_ITEMS.get(item_name)
    if weapon_id is None:
        return
    player.weapon = weapon_id
    player.inventory[item_name] -= 1
    if player.inventory[item_name] <= 0:
        del player.inventory[item_name]



def record_audio_to_file(filename, duration=3, samplerate=44100):
    print(f"[녹음] {duration}초 동안 녹음 시작...")
    recording = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype='int16'
    )
    sd.wait()
    sf.write(filename, recording, samplerate)
    print(f"[녹음] 저장 완료: {filename}")


def use_item(player, item_name):
    if player.inventory.get(item_name, 0) <= 0:
        return
    if item_name in ITEM_USE_FUNCTIONS:
        ITEM_USE_FUNCTIONS[item_name](player)
        return
    if item_name in SPELLBOOK_ITEMS:
        learn_spell_from_book(player, item_name)
        return
    if item_name in WEAPON_ITEMS:
        equip_weapon(player, item_name)
        return

#GPT 작성
def draw_skill_menu(surface, player, target_set, selected_slot):
    menu_w, menu_h = 800, 450
    menu_x = (WIDTH - menu_w) // 2
    menu_y = (HEIGHT - menu_h) // 2
    menu_surf = pygame.Surface((menu_w, menu_h))
    menu_surf.set_alpha(220)
    menu_surf.fill(DARK_GRAY)
    pygame.draw.rect(menu_surf, WHITE, (0, 0, menu_w, menu_h), 3)

    title_font = get_korean_font(36)
    item_font = get_korean_font(24)
    small_font = get_korean_font(18)

    title = "무기 & 마법 선택 (E: 닫기 / 1~4: 슬롯 선택)"
    title_surf = title_font.render(title, True, WHITE)
    menu_surf.blit(title_surf, title_surf.get_rect(center=(menu_w // 2, 40)))

    if player.equipped_spells and 0 <= selected_slot < len(player.equipped_spells):
        sel_id = player.equipped_spells[selected_slot]
        sel_name = SPELL_DISPLAY_NAMES.get(sel_id, sel_id)
        sel_text = small_font.render(f"현재 선택된 마법: {selected_slot+1}번 - {sel_name}", True, YELLOW)
    else:
        sel_text = small_font.render("현재 선택된 마법: 없음", True, LIGHT_GRAY)
    menu_surf.blit(sel_text, (20, 80))

    mp_text = f"MP: {int(player.mp)}/{player.max_mp}"
    mp_surf = small_font.render(mp_text, True, GREEN)
    menu_surf.blit(mp_surf, (20, 105))

    target_text = "타겟: 설정됨 (마우스로 찍음)" if target_set else "타겟: 미설정 (마우스로 찍기)"
    target_color = CYAN if target_set else LIGHT_GRAY
    target_surf = small_font.render(target_text, True, target_color)
    menu_surf.blit(target_surf, (20, 130))

    spell_title = item_font.render("마법 슬롯 (1~4로 선택, Enter로 시전)", True, WHITE)
    menu_surf.blit(spell_title, (40, 160))

    for idx in range(MAX_SPELL_SLOTS):
        y = 200 + idx * 50
        is_selected = (idx == selected_slot)
        color = YELLOW if is_selected else WHITE
        prefix = "▶ " if is_selected else "  "
        slot_label = f"{prefix}{idx+1}. "
        if idx < len(player.equipped_spells):
            spell_id = player.equipped_spells[idx]
            name = SPELL_DISPLAY_NAMES.get(spell_id, spell_id)
            rank = player.known_spells.get(spell_id, "?")
            text = f"{slot_label}{name} ({rank}랭크)"
        else:
            text = f"{slot_label}- 비어 있음 -"
        text_surf = item_font.render(text, True, color)
        menu_surf.blit(text_surf, (40, y))

    weapon_title = item_font.render("현재 무기", True, WHITE)
    menu_surf.blit(weapon_title, (menu_w // 2 + 40, 200))
    text = f"{player.weapon}"
    text_surf = item_font.render(text, True, WHITE)
    menu_surf.blit(text_surf, (menu_w // 2 + 40, 240))
    small = small_font.render("(무기 교체는 인벤토리에서 무기 사용)", True, LIGHT_GRAY)
    menu_surf.blit(small, (menu_w // 2 + 40, 270))

    surface.blit(menu_surf, (menu_x, menu_y))


def show_fireball_intro_and_record(player):
    if "fireball" not in player.known_spells:
        return
    display_name = SPELL_DISPLAY_NAMES.get("fireball", "파이어볼")
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(220)
    overlay.fill(BLACK)

    title_font = get_korean_font(40)
    text_font = get_korean_font(24)
    small_font = get_korean_font(18)

    t1 = title_font.render("당신의 안에서 불소리가 들립니다....", True, ORANGE)
    t2 = text_font.render("기본 마법 '파이어볼'을 사용할 수 있게 되었습니다.", True, WHITE)
    t3 = text_font.render("지금부터 이 마법을 사용할 때 외칠 주문을 직접 녹음할 수 있습니다.", True, WHITE)
    t4 = small_font.render("아무 키나 누르세요....", True, LIGHT_GRAY)

    overlay.blit(t1, t1.get_rect(center=(WIDTH//2, HEIGHT//2 - 80)))
    overlay.blit(t2, t2.get_rect(center=(WIDTH//2, HEIGHT//2 - 30)))
    overlay.blit(t3, t3.get_rect(center=(WIDTH//2, HEIGHT//2 + 10)))
    overlay.blit(t4, t4.get_rect(center=(WIDTH//2, HEIGHT//2 + 70)))
    screen.blit(overlay, (0, 0))
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                waiting = False
                break
        clock.tick(60)

    existing_sound = player.spell_sounds.get("fireball")
    sound = open_spell_sound_popup("fireball", display_name, initial_sound=existing_sound, mode="new")
    if sound is not None:
        player.spell_sounds["fireball"] = sound


def open_spell_sound_popup(spell_id, display_name, initial_sound=None, mode="new"):
    popup_w, popup_h = 700, 380
    popup_x = (WIDTH - popup_w) // 2
    popup_y = (HEIGHT - popup_h) // 2

    title_font = get_korean_font(32)
    text_font = get_korean_font(22)
    small_font = get_korean_font(18)

    current_sound = initial_sound
    has_recorded = False
    is_recording = False
    recorded_chunks = []
    record_stream = None
    record_start_time = 0.0
    max_duration = 3.0
    samplerate = 44100
    frames_per_chunk = int(samplerate * 0.05)

    def start_recording():
        nonlocal is_recording, recorded_chunks, record_stream, record_start_time
        try:
            recorded_chunks = []
            record_stream = sd.InputStream(samplerate=samplerate, channels=1, dtype='int16')
            record_stream.start()
            record_start_time = time.time()
            is_recording = True
            print(f"[녹음] '{display_name}' 녹음 시작 (최대 {max_duration}초)")
        except Exception as e:
            print(f"[녹음] 시작 실패: {e}")
            is_recording = False
            record_stream = None

    def stop_recording():
        nonlocal is_recording, record_stream, recorded_chunks, current_sound, has_recorded
        if not is_recording:
            return
        try:
            if record_stream is not None:
                record_stream.stop()
                record_stream.close()
        except Exception as e:
            print(f"[녹음] 스트림 종료 중 오류: {e}")
        record_stream = None
        is_recording = False
        if not recorded_chunks:
            return
        audio = np.concatenate(recorded_chunks, axis=0)
        filename = os.path.join(SPELL_SOUND_DIR, f"{spell_id}.wav")
        try:
            sf.write(filename, audio, samplerate)
            current_sound = pygame.mixer.Sound(filename)
            has_recorded = True

        except Exception as e:
            print(f"[녹음] 파일 저장/로드 실패: {e}")

    record_btn = Button(popup_x + 40, popup_y + 230, 150, 60, "녹음", BLUE, (0, 150, 255))
    play_btn = Button(popup_x + 220, popup_y + 230, 150, 60, "소리 듣기", GREEN, (0, 180, 0))
    ok_btn = Button(popup_x + 400, popup_y + 230, 120, 60, "확인", ORANGE, (255, 200, 0))
    cancel_btn = Button(popup_x + 540, popup_y + 230, 120, 60, "취소", DARK_RED, (200, 0, 0))

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if is_recording:
                    stop_recording()
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if record_btn.rect.collidepoint(event.pos):
                    if not is_recording:
                        start_recording()
                    else:
                        stop_recording()
                elif play_btn.rect.collidepoint(event.pos):
                    if current_sound is not None:
                        current_sound.play()
                elif ok_btn.rect.collidepoint(event.pos):
                    if is_recording:
                        stop_recording()
                    return current_sound
                elif cancel_btn.rect.collidepoint(event.pos):
                    if is_recording:
                        stop_recording()
                    return initial_sound if mode == "edit" else None

        if is_recording and record_stream is not None:
            try:
                frames, overflowed = record_stream.read(frames_per_chunk)
                recorded_chunks.append(frames.copy())
            except Exception as e:
                print(f"[녹음] 읽기 오류: {e}")
                stop_recording()
            else:
                elapsed = time.time() - record_start_time
                if elapsed >= max_duration:
                    stop_recording()

        record_btn.check_hover(mouse_pos)
        play_btn.check_hover(mouse_pos)
        ok_btn.check_hover(mouse_pos)
        cancel_btn.check_hover(mouse_pos)
        record_btn.text = "녹음 중지" if is_recording else "녹음"

        popup_surf = pygame.Surface((popup_w, popup_h))
        popup_surf.fill(DARK_GRAY)
        pygame.draw.rect(popup_surf, WHITE, (0, 0, popup_w, popup_h), 3)

        if mode == "new":
            title_text = f"새 마법 '{display_name}' 주문 녹음"
        else:
            title_text = f"마법 '{display_name}' 주문 소리 편집"
        title_surf = title_font.render(title_text, True, WHITE)
        popup_surf.blit(title_surf, title_surf.get_rect(center=(popup_w//2, 50)))

        line1 = text_font.render("녹음: 최대 3초 동안 말할 수 있고, 다시 누르면 중지됩니다.", True, WHITE)
        line2 = text_font.render("소리 듣기: 현재 저장된 주문 소리를 들어봅니다.", True, WHITE)
        line3 = small_font.render("마음에 안 들면 재녹음하세요.", True, LIGHT_GRAY)
        popup_surf.blit(line1, (40, 110))
        popup_surf.blit(line2, (40, 140))
        popup_surf.blit(line3, (40, 170))

        if is_recording:
            status_text = "상태: 녹음 중..."
            status_color = YELLOW
        else:
            if current_sound is None:
                status_text = "상태: 녹음된 주문 소리가 없습니다."
                status_color = LIGHT_GRAY
            else:
                status_text = "상태: 주문 소리가 등록되어 있습니다."
                status_color = CYAN if has_recorded else GREEN
        status_surf = text_font.render(status_text, True, status_color)
        popup_surf.blit(status_surf, (40, 200))

        screen.blit(popup_surf, (popup_x, popup_y))
        record_btn.draw(screen)
        play_btn.draw(screen)
        ok_btn.draw(screen)
        cancel_btn.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    if is_recording:
        stop_recording()
    return current_sound


def record_spell_sound_ui(spell_id):
    duration = 3
    message_font = get_korean_font(32)
    small_font = get_korean_font(20)

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill(BLACK)
    text1 = message_font.render("마법 주문 녹음", True, WHITE)
    text2 = small_font.render("마이크에 대고 을 말하세요.", True, WHITE)
    text3 = small_font.render(f"{duration}초 동안 자동 녹음됩니다.", True, CYAN)
    text4 = small_font.render("3...2...1...", True, YELLOW)
    overlay.blit(text1, text1.get_rect(center=(WIDTH//2, HEIGHT//2 - 60)))
    overlay.blit(text2, text2.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))
    overlay.blit(text3, text3.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))
    overlay.blit(text4, text4.get_rect(center=(WIDTH//2, HEIGHT//2 + 60)))
    screen.blit(overlay, (0, 0))
    pygame.display.flip()
    pygame.time.wait(1000)

    filename = os.path.join(SPELL_SOUND_DIR, f"{spell_id}.wav")
    record_audio_to_file(filename, duration=duration, samplerate=44100)

    overlay.fill(BLACK)
    done_text = message_font.render("녹음 완료", True, GREEN)
    tip_text = small_font.render("마법을 사용할 때마다 녹음한 소리가 재생됩니다.", True, WHITE)
    overlay.blit(done_text, done_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))
    overlay.blit(tip_text, tip_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))
    screen.blit(overlay, (0, 0))
    pygame.display.flip()
    pygame.time.wait(800)

    try:
        sound = pygame.mixer.Sound(filename)
        return sound
    except Exception as e:
        print(f"[녹음] 사운드 로드 실패: {e}")
        return None

#GPT 작성
def open_sound_edit_menu(player):
    if not player.known_spells:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(BLACK)
        font = get_korean_font(32)
        small = get_korean_font(20)
        t1 = font.render("배운 마법이 없습니다.", True, WHITE)
        t2 = small.render("소리 교환권이 사용되지 않았습니다.", True, LIGHT_GRAY)
        overlay.blit(t1, t1.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))
        overlay.blit(t2, t2.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        pygame.time.wait(1000)
        return False

    spell_ids = list(player.known_spells.keys())
    selected = 0
    running = True
    title_font = get_korean_font(34)
    item_font = get_korean_font(24)
    small_font = get_korean_font(18)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(spell_ids)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(spell_ids)
                elif event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                    spell_id = spell_ids[selected]
                    display_name = SPELL_DISPLAY_NAMES.get(spell_id, spell_id)
                    existing_sound = player.spell_sounds.get(spell_id)
                    sound = open_spell_sound_popup(spell_id, display_name, initial_sound=existing_sound, mode="edit")
                    if sound is not None:
                        player.spell_sounds[spell_id] = sound
                        return True
                    else:
                        print("[소리 교환권] 주문 소리 변경이 취소되었습니다.")

        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(230)
        overlay.fill(DARK_GRAY)
        title = title_font.render("소리 교환권 - 마법 선택", True, WHITE)
        overlay.blit(title, title.get_rect(center=(WIDTH//2, 120)))

        info1 = small_font.render("↑/↓ : 마법 선택", True, WHITE)
        info2 = small_font.render("Enter : 선택한 마법의 주문 소리 편집", True, YELLOW)
        info3 = small_font.render("ESC : 취소 (교환권 유지)", True, LIGHT_GRAY)
        overlay.blit(info1, (WIDTH//2 - 220, 170))
        overlay.blit(info2, (WIDTH//2 - 220, 200))
        overlay.blit(info3, (WIDTH//2 - 220, 230))

        start_y = 280
        line_h = 35
        for idx, spell_id in enumerate(spell_ids):
            name = SPELL_DISPLAY_NAMES.get(spell_id, spell_id)
            rank = player.known_spells.get(spell_id, "?")
            prefix = "▶ " if idx == selected else "  "
            color = YELLOW if idx == selected else WHITE
            text = f"{prefix}{name} ({rank}랭크)"
            surf = item_font.render(text, True, color)
            overlay.blit(surf, (WIDTH//2 - 200, start_y + idx * line_h))

        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(60)


def use_sound_ticket(player):
    print("[소리 교환권] 사용 시도")
    used = open_sound_edit_menu(player)
    if used:
        player.inventory["소리 교환권"] -= 1
        if player.inventory["소리 교환권"] <= 0:
            del player.inventory["소리 교환권"]
        print("[소리 교환권] 1장을 사용했습니다.")
    else:
        print("[소리 교환권] 사용이 취소되었습니다.")


ITEM_USE_FUNCTIONS["소리 교환권"] = use_sound_ticket


def map_transition_effect(text="맵 이동 중..."):
    fade_surf = pygame.Surface((WIDTH, HEIGHT))
    fade_surf.fill(BLACK)
    font = get_korean_font(50)
    text_surf = font.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    for alpha in range(0, 256, 15):
        fade_surf.set_alpha(alpha)
        screen.blit(fade_surf, (0, 0))
        screen.blit(text_surf, text_rect)
        pygame.display.flip()
        clock.tick(30)
    pygame.time.wait(200)
    for alpha in range(255, -1, -15):
        fade_surf.set_alpha(alpha)
        screen.fill(BLACK)
        screen.blit(fade_surf, (0, 0))
        pygame.display.flip()
        clock.tick(60)



def main():
    global VOLUME
    gender = character_selection()

    game_maps = {}
    show_inventory = False
    show_skill_menu = False
    xp_orbs = []
    item_drops = []
    selected_spell_slot = 0
    auto_targeting = False
    show_setting = False

    volume = VOLUME
    dragging_volume = False
    volume_slider_rect = None

    show_swap_menu = False
    swap_phase = 0
    swap_selected_slot = 0
    swap_selected_index = 0
    swap_unequipped_spells = []

    if os.path.exists("house.tmx") and os.path.exists("map.tmx"):
        try:
            tmx_house = TiledMap("house.tmx")
            tmx_map = TiledMap("map.tmx")
            game_maps["house"] = GameMap("house", tmx_house)
            game_maps["map"] = GameMap("map", tmx_map)
            print("house.tmx, map.tmx 로드 성공!")
        except Exception as e:
            print(f"TMX 로드 실패: {e}.")
            game_maps = None
    elif os.path.exists("map.tmx"):
        try:
            tmx_map = TiledMap("map.tmx")
            game_maps["map"] = GameMap("map", tmx_map)
            print("map.tmx 로드 성공!")
        except Exception as e:
            print(f"TMX 로드 실패: {e}.")
            game_maps = None
    else:
        game_maps = None

    if game_maps and "house" in game_maps:
        current_map_name = "house"
    elif game_maps:
        current_map_name = "map"
    else:
        current_map_name = None

    current_map = game_maps[current_map_name] if current_map_name else None
    spawn_x, spawn_y = current_map.tiled_map.find_player_spawn() if current_map else (WIDTH // 2, HEIGHT // 2)
    player = Player(spawn_x, spawn_y, gender)
    camera = Camera(WIDTH, HEIGHT)

    def update_camera_offset():
        if current_map and current_map.tiled_map:
            map_w = current_map.tiled_map.pixel_w
            map_h = current_map.tiled_map.pixel_h
            camera.offset_x = max(0, (WIDTH - map_w) // 2)
            camera.offset_y = max(0, (HEIGHT - map_h) // 2)
        else:
            camera.offset_x = 0
            camera.offset_y = 0

    player_spells, enemy_projectiles = [], []
    target_position = None

    enemy_factory = {
        "slime": lambda x, y, level=1: Slime(x, y, level),
        "dummy": lambda x, y, level=None: Dummy(x, y),
    }

    def spawn_enemies_on_map(cmap):
        if cmap and not cmap.enemies_spawned:
            enemy_spawns = cmap.tiled_map.find_enemy_spawns()
            for ex, ey, etype, level in enemy_spawns:
                if etype in enemy_factory:
                    cmap.enemies.append(enemy_factory[etype](ex, ey, level))
            cmap.enemies_spawned = True

    spawn_enemies_on_map(current_map)
    fireball_intro_done = False
    running = True

    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if show_swap_menu:
                    if event.key == pygame.K_ESCAPE:
                        show_swap_menu = False
                    elif swap_phase == 0:
                        if pygame.K_1 <= event.key <= pygame.K_4:
                            idx = event.key - pygame.K_1
                            if 0 <= idx < MAX_SPELL_SLOTS:
                                swap_selected_slot = idx
                        if event.key in (pygame.K_UP, pygame.K_w):
                            swap_selected_slot = (swap_selected_slot - 1) % MAX_SPELL_SLOTS
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            swap_selected_slot = (swap_selected_slot + 1) % MAX_SPELL_SLOTS
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            swap_phase = 1
                    else:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            if swap_unequipped_spells:
                                swap_selected_index = (swap_selected_index - 1) % len(swap_unequipped_spells)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            if swap_unequipped_spells:
                                swap_selected_index = (swap_selected_index + 1) % len(swap_unequipped_spells)
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if swap_unequipped_spells:
                                new_spell = swap_unequipped_spells[swap_selected_index]
                                if swap_selected_slot >= len(player.equipped_spells):
                                    if len(player.equipped_spells) < MAX_SPELL_SLOTS:
                                        player.equipped_spells.append(new_spell)
                                else:
                                    player.equipped_spells[swap_selected_slot] = new_spell
                                selected_spell_slot = swap_selected_slot
                            show_swap_menu = False
                    continue

                if event.key == pygame.K_i:
                    show_inventory = not show_inventory
                    if show_inventory:
                        show_skill_menu = False
                        show_setting = False
                elif event.key == pygame.K_e:
                    show_skill_menu = not show_skill_menu
                    if show_skill_menu:
                        show_inventory = False
                        show_setting = False
                elif event.key == pygame.K_ESCAPE and (show_inventory or show_skill_menu or show_setting):
                    show_inventory = False
                    show_skill_menu = False
                    show_setting = False
                elif event.key == pygame.K_ESCAPE:
                    show_setting = not show_setting

                if event.key == pygame.K_v:
                    auto_targeting = not auto_targeting
                    if not auto_targeting:
                        target_position = None

                if show_inventory:
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        index = event.key - pygame.K_1
                        items = list(player.inventory.keys())
                        if 0 <= index < len(items):
                            item_name = items[index]
                            use_item(player, item_name)
                        continue

                if show_skill_menu:
                    if pygame.K_1 <= event.key <= pygame.K_4:
                        index = event.key - pygame.K_1
                        if 0 <= index < len(player.equipped_spells):
                            selected_spell_slot = index
                        continue

                    if event.key in (pygame.K_UP, pygame.K_w):
                        if player.equipped_spells:
                            selected_spell_slot = (selected_spell_slot - 1) % len(player.equipped_spells)
                        continue

                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        if player.equipped_spells:
                            selected_spell_slot = (selected_spell_slot + 1) % len(player.equipped_spells)
                        continue

                    if event.key == pygame.K_m and not show_swap_menu:
                        spells = list(player.known_spells.keys())
                        equipped_set = set(player.equipped_spells[:MAX_SPELL_SLOTS])
                        swap_unequipped_spells = [sid for sid in spells if sid not in equipped_set]

                        if not swap_unequipped_spells:
                            overlay = pygame.Surface((WIDTH, HEIGHT))
                            overlay.set_alpha(220)
                            overlay.fill(BLACK)
                            font = get_korean_font(32)
                            small = get_korean_font(20)
                            t1 = font.render("장착되지 않은 마법이 없습니다.", True, WHITE)
                            t2 = small.render("새로 끼울 마법이 없습니다.", True, LIGHT_GRAY)
                            overlay.blit(t1, t1.get_rect(center=(WIDTH//2, HEIGHT//2 - 20)))
                            overlay.blit(t2, t2.get_rect(center=(WIDTH//2, HEIGHT//2 + 20)))
                            screen.blit(overlay, (0, 0))
                            pygame.display.flip()
                            pygame.time.wait(1000)
                        else:
                            show_swap_menu = True
                            swap_phase = 0
                            swap_selected_slot = selected_spell_slot
                            swap_selected_index = 0
                        continue

                if pygame.K_1 <= event.key <= pygame.K_4:
                    index = event.key - pygame.K_1
                    if 0 <= index < len(player.equipped_spells):
                        selected_spell_slot = index
                        sel_spell = player.equipped_spells[index]

                if event.key == pygame.K_SPACE and target_position:
                    if player.equipped_spells:
                        if 0 <= selected_spell_slot < len(player.equipped_spells):
                            slot_index = selected_spell_slot
                        else:
                            slot_index = 0
                        spell_id = player.equipped_spells[slot_index]
                        spell = player.cast_spell(target_position, spell_type=spell_id, current_map=current_map)
                        if spell:
                            player_spells.append(spell)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and target_position and not show_inventory and not show_skill_menu and not show_swap_menu:
                    if player.equipped_spells:
                        if 0 <= selected_spell_slot < len(player.equipped_spells):
                            slot_index = selected_spell_slot
                        else:
                            slot_index = 0
                        spell_id = player.equipped_spells[slot_index]
                        spell = player.cast_spell(target_position, spell_type=spell_id, current_map=current_map)
                        if spell:
                            player_spells.append(spell)

                if show_setting and event.button == 1:
                    if volume_slider_rect and volume_slider_rect.collidepoint(event.pos):
                        dragging_volume = True
                        rel = (event.pos[0] - volume_slider_rect.x) / volume_slider_rect.width
                        volume = max(0.0, min(1.0, rel))
                        VOLUME = volume
                        pygame.mixer.music.set_volume(volume)
                        for sound in player.spell_sounds.values():
                            sound.set_volume(volume)

                if event.button == 3 and not show_inventory:
                    mx, my = pygame.mouse.get_pos()
                    target_position = (mx + camera.x, my + camera.y)

            elif event.type == pygame.MOUSEBUTTONUP:
                if show_setting and event.button == 1:
                    dragging_volume = False

            elif event.type == pygame.MOUSEMOTION:
                if show_setting and dragging_volume and volume_slider_rect:
                    rel = (event.pos[0] - volume_slider_rect.x) / volume_slider_rect.width
                    volume = max(0.0, min(1.0, rel))
                    VOLUME = volume
                    pygame.mixer.music.set_volume(volume)
                    for sound in player.spell_sounds.values():
                        sound.set_volume(volume)

        keys = pygame.key.get_pressed()
        player.move(keys, current_map.tiled_map if current_map else None)
        player.regen_mp()

        camera.update(player)
        if current_map:
            current_map.tiled_map.clamp_camera(camera)

        if auto_targeting and current_map and current_map.enemies:
            closest_enemy = None
            closest_dist = float('inf')
            px = player.x + player.width / 2
            py = player.y + player.height / 2
            for enemy in current_map.enemies:
                if isinstance(enemy, Slime) and enemy.dying:
                    continue
                if enemy.hp <= 0 and not enemy.is_dummy:
                    continue
                ex = enemy.x + enemy.width / 2
                ey = enemy.y + enemy.height / 2
                dist = math.hypot(ex - px, ey - py)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_enemy = enemy
            if closest_enemy:
                target_position = (
                    closest_enemy.x + closest_enemy.width / 2,
                    closest_enemy.y + closest_enemy.height / 2
                )
            else:
                target_position = None

        if current_map and game_maps:
            player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
            for portal in current_map.portals:
                if player_rect.colliderect(portal["rect"]):
                    target_name = portal["portal_type"]
                    if not target_name:
                        break
                    if target_name not in game_maps:
                        break
                    target_map = game_maps[target_name]
                    sx, sy = target_map.tiled_map.find_player_spawn()
                    player.x, player.y = sx, sy
                    map_transition_effect(f"{target_name}(으)로 이동!")
                    current_map_name = target_name
                    current_map = target_map
                    update_camera_offset()
                    player_spells.clear()
                    enemy_projectiles.clear()
                    target_position = None
                    item_drops.clear()
                    spawn_enemies_on_map(current_map)

                    if current_map_name == "map" and not fireball_intro_done:
                        show_fireball_intro_and_record(player)
                        fireball_intro_done = True
                    break

        if current_map:
            for enemy in current_map.enemies[:]:
                enemy.update(player, current_map.tiled_map, enemy_projectiles, current_map.damage_texts)

                if isinstance(enemy, Slime):
                    if enemy.death_finished:
                        drop_x = enemy.x + enemy.width / 2
                        drop_y = enemy.y + enemy.height / 2
                        level = getattr(enemy, "level", 1)
                        xp_value = 5 + 5 * level * (1.1 ** level)
                        xp_orbs.append(XPOrb(drop_x, drop_y, value=xp_value))

                        if random.random() < 0.5:
                            names = [item[0] for item in SLIME_SPELLBOOK_DROPS]
                            weights = [item[1] for item in SLIME_SPELLBOOK_DROPS]
                            item_name = random.choices(names, weights=weights, k=1)[0]
                            item_drops.append(ItemDrop(drop_x, drop_y, item_name))

                        if random.random() < 0.05:
                            item_drops.append(ItemDrop(drop_x, drop_y, "소리 교환권"))

                        respawn_delay = 300
                        etype = enemy.enemy_type
                        if etype in enemy_factory:
                            current_map.respawn_queue.append({
                                "timer": respawn_delay,
                                "x": enemy.home_x,
                                "y": enemy.home_y,
                                "type": etype,
                                "level": getattr(enemy, "level", 1),
                            })
                        current_map.enemies.remove(enemy)

                elif isinstance(enemy, Dummy):
                    pass

                else:
                    if enemy.hp <= 0:
                        drop_x = enemy.x + enemy.width / 2
                        drop_y = enemy.y + enemy.height / 2

                        respawn_delay = 300
                        etype = getattr(enemy, "enemy_type", None)
                        if etype in enemy_factory:
                            current_map.respawn_queue.append({
                                "timer": respawn_delay,
                                "x": enemy.home_x,
                                "y": enemy.home_y,
                                "type": etype,
                            })
                            print(f"[DEBUG] {etype} 리스폰 예약: {respawn_delay}틱 후 ({enemy.home_x}, {enemy.home_y})")
                        current_map.enemies.remove(enemy)

            for entry in current_map.respawn_queue[:]:
                entry["timer"] -= 1
                if entry["timer"] <= 0:
                    etype = entry["type"]
                    ex, ey = entry["x"], entry["y"]
                    level = entry.get("level", 1)
                    if etype in enemy_factory:
                        new_enemy = enemy_factory[etype](ex, ey, level)
                        current_map.enemies.append(new_enemy)
                        print(f"[DEBUG] {etype}(Lv.{level}) 리스폰! 위치=({ex}, {ey})")
                    current_map.respawn_queue.remove(entry)

            for chain in current_map.lightning_chains[:]:
                chain.update(current_map.enemies, current_map.damage_texts)
                if not chain.active:
                    current_map.lightning_chains.remove(chain)

            for dmg_text in current_map.damage_texts[:]:
                dmg_text.update()
                if not dmg_text.active:
                    current_map.damage_texts.remove(dmg_text)

        for spell in player_spells[:]:
            spell.update()
            if not spell.active:
                player_spells.remove(spell)
                continue

            if current_map:
                for enemy in current_map.enemies:
                    if math.hypot(
                        spell.x - (enemy.x + enemy.width / 2),
                        spell.y - (enemy.y + enemy.height / 2)
                    ) < spell.radius + enemy.width / 2:
                        enemy.hp -= spell.damage
                        current_map.damage_texts.append(DamageText(
                            enemy.x + enemy.width / 2,
                            enemy.y,
                            spell.damage
                        ))

                        if spell.spell_type == "fireball":
                            enemy.apply_burn(duration=600, total_damage=50)
                        elif spell.spell_type == "ice_lans":
                            enemy.apply_ice_hit()
                        elif spell.spell_type == "lightning_bolt":
                            chain = LightningChain(
                                enemy.x + enemy.width / 2,
                                enemy.y + enemy.height / 2,
                                spell.damage * 0.7,
                                [id(enemy)]
                            )
                            current_map.lightning_chains.append(chain)
                            print(f"[번개] 체인 생성!")
                        elif spell.spell_type == "water_blast":
                            enemy.apply_slow(duration=300)

                        spell.active = False
                        break

        for proj in enemy_projectiles[:]:
            proj.update()
            if not proj.active:
                enemy_projectiles.remove(proj)
                continue
            if pygame.Rect(player.x, player.y, player.width, player.height).colliderect(
                pygame.Rect(proj.x - proj.radius, proj.y - proj.radius, proj.radius * 2, proj.radius * 2)
            ):
                player.hp -= proj.damage
                proj.active = False

        for drop in item_drops[:]:
            if pygame.Rect(player.x, player.y, player.width, player.height).colliderect(drop.get_rect()):
                player.inventory[drop.item_name] = player.inventory.get(drop.item_name, 0) + 1
                print(f"'{drop.item_name}' 을(를) 주웠습니다!")
                item_drops.remove(drop)

        for orb in xp_orbs[:]:
            orb.update(player)
            px = player.x + player.width / 2
            py = player.y + player.height / 2
            if math.hypot(orb.x - px, orb.y - py) < orb.radius + player.width / 3:
                player.add_xp(orb.value)
                xp_orbs.remove(orb)

        if player.hp <= 0:
            screen.fill(BLACK)
            text = get_korean_font(50).render("게임 오버!", True, RED)
            screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            pygame.display.flip()
            pygame.time.wait(3000)
            running = False

        screen.fill(BLACK)

        if current_map:
            current_map.tiled_map.draw(screen, camera)
            for eff in current_map.area_effects:
                eff.draw(screen, camera)

        if target_position:
            draw_target_marker(screen, camera, *target_position)

        player.draw(screen, camera)

        if current_map:
            for enemy in current_map.enemies:
                enemy.draw(screen, camera)
            for chain in current_map.lightning_chains:
                chain.draw(screen, camera)
            for dmg_text in current_map.damage_texts:
                dmg_text.draw(screen, camera)
            for eff in current_map.area_effects[:]:
                eff.update(current_map)
                if not eff.active:
                    current_map.area_effects.remove(eff)

        for drop in item_drops:
            drop.draw(screen, camera)

        for orb in xp_orbs:
            orb.draw(screen, camera)

        for spell in player_spells:
            spell.draw(screen, camera)

        for proj in enemy_projectiles:
            proj.draw(screen, camera)

        if current_map:
            draw_ui(screen, player, current_map, target_position is not None)

        if show_inventory:
            draw_inventory(screen, player)

        if show_setting:
            volume_slider_rect = draw_setting(screen, volume)
        else:
            volume_slider_rect = None

        if show_skill_menu:
            draw_skill_menu(screen, player, target_position is not None, selected_spell_slot)

        if show_swap_menu:
            draw_swap_menu(
                screen,
                player,
                swap_phase,
                swap_selected_slot,
                swap_selected_index,
                swap_unequipped_spells
            )

        pygame.display.flip()

    pygame.quit()



if __name__ == "__main__":
    load_slime_frames()
    main()