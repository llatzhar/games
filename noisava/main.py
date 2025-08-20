import pyxel
import math
import random
from enum import Enum
from abc import ABC, abstractmethod


# ゲーム定数
SPRITE_SIZE = 8  # キャラクタのスプライトサイズ (8x8)
SCREEN_WIDTH = 160
SCREEN_HEIGHT = 120


class GameState(Enum):
    TITLE = 0
    GAME = 1
    LEVEL_UP = 2
    PAUSE = 3
    GAME_OVER = 4
    CLEAR = 5


class CompanionType(Enum):
    BASIC_SHOT = 0      # 基本弾
    RAPID_SHOT = 1      # 連射弾
    SPREAD_SHOT = 2     # 拡散弾
    MULTICAST = 3       # マルチキャスト（効果）
    POWER_UP = 4        # 威力強化（効果）
    HOMING = 5          # 追尾効果（効果）


class Scene(ABC):
    @abstractmethod
    def update(self):
        pass
    
    @abstractmethod
    def draw(self):
        pass


class Vec2:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vec2(self.x * scalar, self.y * scalar)
    
    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def normalize(self):
        l = self.length()
        if l > 0:
            return Vec2(self.x / l, self.y / l)
        return Vec2(0, 0)
    
    def distance_to(self, other):
        return (self - other).length()


class GameObject:
    def __init__(self, pos, size=SPRITE_SIZE):
        self.pos = pos
        self.size = size
        self.alive = True
    
    def get_rect(self):
        return (self.pos.x, self.pos.y, self.size, self.size)
    
    def collides_with(self, other):
        r1 = self.get_rect()
        r2 = other.get_rect()
        return (r1[0] < r2[0] + r2[2] and
                r1[0] + r1[2] > r2[0] and
                r1[1] < r2[1] + r2[3] and
                r1[1] + r1[3] > r2[1])


class Companion:
    def __init__(self, companion_type, level=1):
        self.type = companion_type
        self.level = level
        self.name = self.get_name()
        self.description = self.get_description()
    
    def get_name(self):
        names = {
            CompanionType.BASIC_SHOT: "Basic", #"ベーシックショット",
            CompanionType.RAPID_SHOT: "Rapid", #"ラピッドショット", 
            CompanionType.SPREAD_SHOT: "Spread", #"スプレッドショット",
            CompanionType.MULTICAST: "Multicast", #"マルチキャスト",
            CompanionType.POWER_UP: "Power", #"パワーアップ",
            CompanionType.HOMING: "Homing" #"ホーミング"
        }
        return names.get(self.type, "不明")
    
    def get_description(self):
        descriptions = {
            CompanionType.BASIC_SHOT: "基本的な弾を発射する",
            CompanionType.RAPID_SHOT: "高速で連射する弾",
            CompanionType.SPREAD_SHOT: "3方向に拡散する弾",
            CompanionType.MULTICAST: "次の仲間を2回発動",
            CompanionType.POWER_UP: "次の仲間の威力を2倍",
            CompanionType.HOMING: "次の仲間に追尾効果付与"
        }
        return descriptions.get(self.type, "")


class Player(GameObject):
    def __init__(self, pos):
        super().__init__(pos)
        self.max_hp = 100
        self.hp = self.max_hp
        self.speed = 1.5
        self.level = 1
        self.exp = 0
        self.exp_to_next = 10
        self.sprite_x = 0
        self.sprite_y = 0
        self.attack_cooldown = 0
        self.companions = [Companion(CompanionType.BASIC_SHOT)]  # 初期仲間
    
    def update(self):
        # 移動
        dx = 0
        dy = 0
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
            dx -= self.speed
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
            dx += self.speed
        if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W):
            dy -= self.speed
        if pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S):
            dy += self.speed
        
        # 画面内に制限
        self.pos.x = max(0, min(SCREEN_WIDTH - self.size, self.pos.x + dx))
        self.pos.y = max(0, min(SCREEN_HEIGHT - self.size, self.pos.y + dy))
        
        # 攻撃クールダウン更新
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
    
    def gain_exp(self, amount):
        self.exp += amount
        if self.exp >= self.exp_to_next:
            self.level_up()
            return True
        return False
    
    def level_up(self):
        self.level += 1
        self.exp = 0
        self.exp_to_next = int(self.exp_to_next * 1.5)
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False
    
    def add_companion(self, companion):
        self.companions.append(companion)
    
    def draw(self):
        pyxel.blt(self.pos.x, self.pos.y, 0, self.sprite_x, self.sprite_y, SPRITE_SIZE, SPRITE_SIZE)


class Enemy(GameObject):
    def __init__(self, pos, enemy_type=0):
        super().__init__(pos)
        self.enemy_type = enemy_type
        self.speed = 0.5
        self.hp = 10
        self.max_hp = 10
        self.damage = 10
        self.exp_value = 1
        
        # 敵タイプ別設定
        if enemy_type == 0:
            self.sprite_x = 0
            self.sprite_y = 32
        elif enemy_type == 1:
            self.sprite_x = 8
            self.sprite_y = 32
            self.speed = 0.3
            self.hp = 20
            self.max_hp = 20
            self.damage = 15
            self.exp_value = 2
    
    def update(self, player_pos):
        # プレイヤーに向かって移動
        direction = (player_pos - self.pos).normalize()
        self.pos = self.pos + direction * self.speed
    
    def take_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.alive = False
    
    def draw(self):
        pyxel.blt(self.pos.x, self.pos.y, 0, self.sprite_x, self.sprite_y, SPRITE_SIZE, SPRITE_SIZE)


class Bullet(GameObject):
    def __init__(self, pos, direction, speed=3.0, damage=10, homing=False):
        super().__init__(pos)
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.homing = homing
        self.sprite_x = 0
        self.sprite_y = 16
        self.lifetime = 120  # フレーム数
    
    def update(self, enemies=None):
        if self.homing and enemies:
            # 最も近い敵に向かって軌道修正
            closest_enemy = min(enemies, key=lambda e: self.pos.distance_to(e.pos))
            if self.pos.distance_to(closest_enemy.pos) > 0:
                target_dir = (closest_enemy.pos - self.pos).normalize()
                # 緩やかに軌道修正
                self.direction = (self.direction * 0.8 + target_dir * 0.2).normalize()
        
        self.pos = self.pos + self.direction * self.speed
        self.lifetime -= 1
        
        # 画面外または寿命切れで削除
        if (self.pos.x < -self.size or self.pos.x > SCREEN_WIDTH or
            self.pos.y < -self.size or self.pos.y > SCREEN_HEIGHT or
            self.lifetime <= 0):
            self.alive = False
    
    def draw(self):
        pyxel.blt(self.pos.x, self.pos.y, 0, self.sprite_x, self.sprite_y, SPRITE_SIZE, SPRITE_SIZE)


class Item(GameObject):
    def __init__(self, pos, item_type=0):
        super().__init__(pos)
        self.item_type = item_type  # 0: 経験値, 1: 回復
        
        if item_type == 0:  # 経験値
            self.sprite_x = 0
            self.sprite_y = 48
            self.value = 1
        elif item_type == 1:  # 回復
            self.sprite_x = 8
            self.sprite_y = 48
            self.value = 20
    
    def draw(self):
        pyxel.blt(self.pos.x, self.pos.y, 0, self.sprite_x, self.sprite_y, SPRITE_SIZE, SPRITE_SIZE)


class TitleScene(Scene):
    def __init__(self, game):
        self.game = game
    
    def update(self):
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
            self.game.change_scene(GameState.GAME)
    
    def draw(self):
        pyxel.cls(0)
        pyxel.text(40, 60, "NOISAVA", 7)
        pyxel.text(20, 80, "Press SPACE to Start", 7)
        pyxel.text(30, 100, "WASD/Arrow Keys to Move", 7)


class LevelUpScene(Scene):
    def __init__(self, game, game_scene):
        self.game = game
        self.game_scene = game_scene
        self.available_companions = self.get_random_companions()
        self.selected_index = 0
    
    def get_random_companions(self):
        all_types = list(CompanionType)
        return [Companion(random.choice(all_types)) for _ in range(3)]
    
    def update(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.selected_index = (self.selected_index - 1) % 3
        elif pyxel.btnp(pyxel.KEY_DOWN):
            self.selected_index = (self.selected_index + 1) % 3
        elif pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
            # 選択した仲間を追加
            selected_companion = self.available_companions[self.selected_index]
            self.game_scene.player.add_companion(selected_companion)
            self.game.change_scene(GameState.GAME)
    
    def draw(self):
        # ゲーム画面を暗く描画
        self.game_scene.draw()
        pyxel.rect(0, 0, pyxel.width, pyxel.height, 1)  # 半透明の代わりに青
        
        # レベルアップ画面
        pyxel.rect(20, 30, 120, 80, 0)
        pyxel.rect(21, 31, 118, 78, 7)
        
        pyxel.text(25, 35, "LEVEL UP! Choose Companion:", 0)
        
        for i, companion in enumerate(self.available_companions):
            y = 45 + i * 20
            color = 8 if i == self.selected_index else 0
            pyxel.text(25, y, f"{companion.name}", color)
            pyxel.text(25, y + 8, f"{companion.description}", color)
        
        pyxel.text(25, 105, "UP/DOWN: Select, SPACE: Choose", 0)


class GameScene(Scene):
    def __init__(self, game):
        self.game = game
        self.player = Player(Vec2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.enemies = []
        self.bullets = []
        self.items = []
        self.enemy_spawn_timer = 0
        self.game_timer = 0
        self.survival_time = 300 * 60  # 5分 = 300秒 * 60フレーム
        
    def update(self):
        if pyxel.btnp(pyxel.KEY_P):
            self.game.change_scene(GameState.PAUSE)
            return
        
        self.game_timer += 1
        
        # プレイヤー更新
        self.player.update()
        
        # 敵のスポーン
        self.enemy_spawn_timer += 1
        spawn_rate = max(30, 30 - self.game_timer // 3600)  # 時間経過で敵出現頻度増加
        if self.enemy_spawn_timer >= spawn_rate:
            self.spawn_enemy()
            self.enemy_spawn_timer = 0
        
        # 自動攻撃
        if self.player.attack_cooldown <= 0:
            self.auto_attack()
            self.player.attack_cooldown = 30  # 0.5秒間隔
        
        # 敵更新
        for enemy in self.enemies[:]:
            enemy.update(self.player.pos)
            if not enemy.alive:
                # アイテムドロップ
                if random.random() < 0.1:  # 10%の確率で回復
                    self.items.append(Item(Vec2(enemy.pos.x, enemy.pos.y), 1))
                else:
                    self.items.append(Item(Vec2(enemy.pos.x, enemy.pos.y), 0))
                self.enemies.remove(enemy)
        
        # 弾丸更新
        for bullet in self.bullets[:]:
            bullet.update(self.enemies)
            if not bullet.alive:
                self.bullets.remove(bullet)
        
        # 衝突判定
        self.check_collisions()
        
        # ゲームオーバー判定
        if not self.player.alive:
            self.game.change_scene(GameState.GAME_OVER)
        elif self.game_timer >= self.survival_time:
            self.game.change_scene(GameState.CLEAR)
    
    def spawn_enemy(self):
        # 画面外からランダムに敵をスポーン
        side = random.randint(0, 3)
        if side == 0:  # 上
            pos = Vec2(random.randint(0, SCREEN_WIDTH), -SPRITE_SIZE)
        elif side == 1:  # 右
            pos = Vec2(SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT))
        elif side == 2:  # 下
            pos = Vec2(random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT)
        else:  # 左
            pos = Vec2(-SPRITE_SIZE, random.randint(0, SCREEN_HEIGHT))
        
        enemy_type = 0 if random.random() < 0.8 else 1
        self.enemies.append(Enemy(pos, enemy_type))
    
    def auto_attack(self):
        # 仲間システムを使用した攻撃
        if not self.enemies:
            return
        
        closest_enemy = min(self.enemies, key=lambda e: self.player.pos.distance_to(e.pos))
        base_direction = (closest_enemy.pos - self.player.pos).normalize()
        bullet_pos = Vec2(self.player.pos.x + SPRITE_SIZE//2, self.player.pos.y + SPRITE_SIZE//2)
        
        # 仲間の効果を適用
        self.process_companions(bullet_pos, base_direction)
    
    def process_companions(self, pos, direction):
        # 仲間の効果を順番に処理（簡易版）
        multicast_count = 1
        damage_multiplier = 1.0
        homing = False
        
        # エフェクト系の仲間をまず処理
        for companion in self.player.companions:
            if companion.type == CompanionType.MULTICAST:
                multicast_count *= 2
            elif companion.type == CompanionType.POWER_UP:
                damage_multiplier *= 2.0
            elif companion.type == CompanionType.HOMING:
                homing = True
        
        # 攻撃系の仲間で弾を生成
        for companion in self.player.companions:
            if companion.type in [CompanionType.BASIC_SHOT, CompanionType.RAPID_SHOT, CompanionType.SPREAD_SHOT]:
                for _ in range(multicast_count):
                    self.create_bullets_for_companion(companion, pos, direction, damage_multiplier, homing)
    
    def create_bullets_for_companion(self, companion, pos, direction, damage_multiplier, homing):
        base_damage = int(10 * damage_multiplier)
        
        if companion.type == CompanionType.BASIC_SHOT:
            bullet = Bullet(Vec2(pos.x, pos.y), direction, damage=base_damage, homing=homing)
            self.bullets.append(bullet)
        
        elif companion.type == CompanionType.RAPID_SHOT:
            # 少し弱いが高速な弾
            bullet = Bullet(Vec2(pos.x, pos.y), direction, speed=5.0, damage=max(1, base_damage // 2), homing=homing)
            self.bullets.append(bullet)
        
        elif companion.type == CompanionType.SPREAD_SHOT:
            # 3方向に拡散
            angles = [-0.3, 0, 0.3]  # ラジアン
            for angle in angles:
                spread_dir = Vec2(
                    direction.x * math.cos(angle) - direction.y * math.sin(angle),
                    direction.x * math.sin(angle) + direction.y * math.cos(angle)
                )
                bullet = Bullet(Vec2(pos.x, pos.y), spread_dir, damage=max(1, base_damage // 2), homing=homing)
                self.bullets.append(bullet)
    
    def check_collisions(self):
        # プレイヤーと敵の衝突
        for enemy in self.enemies:
            if self.player.collides_with(enemy):
                self.player.take_damage(enemy.damage)
                enemy.alive = False
        
        # 弾丸と敵の衝突
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if bullet.collides_with(enemy):
                    enemy.take_damage(bullet.damage)
                    bullet.alive = False
                    break
        
        # プレイヤーとアイテムの衝突
        for item in self.items[:]:
            if self.player.collides_with(item):
                if item.item_type == 0:  # 経験値
                    if self.player.gain_exp(item.value):
                        # レベルアップした場合
                        self.game.change_scene(GameState.LEVEL_UP)
                elif item.item_type == 1:  # 回復
                    self.player.hp = min(self.player.max_hp, self.player.hp + item.value)
                self.items.remove(item)
    
    def draw(self):
        pyxel.cls(1)
        
        # ゲームオブジェクト描画
        self.player.draw()
        
        for enemy in self.enemies:
            enemy.draw()
        
        for bullet in self.bullets:
            bullet.draw()
        
        for item in self.items:
            item.draw()
        
        # UI描画
        self.draw_ui()
    
    def draw_ui(self):
        # HP バー
        pyxel.rect(5, 5, 50, 6, 0)
        hp_width = int(48 * self.player.hp / self.player.max_hp)
        pyxel.rect(6, 6, hp_width, 4, 8)
        pyxel.text(5, 12, f"HP: {self.player.hp}/{self.player.max_hp}", 7)
        
        # レベルと経験値
        pyxel.text(5, 20, f"Lv.{self.player.level}", 7)
        exp_width = int(30 * self.player.exp / self.player.exp_to_next)
        pyxel.rect(25, 20, 32, 6, 0)
        pyxel.rect(26, 21, exp_width, 4, 11)
        
        # タイマー
        remaining = max(0, self.survival_time - self.game_timer)
        minutes = remaining // 3600
        seconds = (remaining % 3600) // 60
        pyxel.text(5, 30, f"Time: {minutes:02d}:{seconds:02d}", 7)
        
        # 敵の数
        pyxel.text(5, 40, f"Enemies: {len(self.enemies)}", 7)
        
        # 仲間数
        pyxel.text(5, 50, f"Companions: {len(self.player.companions)}", 7)


class CompanionEditor:
    def __init__(self):
        self.companion_slots = [None] * 8  # 8個のスロット
        self.available_companions = self.get_all_companions()
        self.dragging = None
        self.drag_offset = Vec2(0, 0)
        self.slot_width = SPRITE_SIZE * 2  # スロットサイズをスプライトサイズの2倍に
        self.slot_height = SPRITE_SIZE * 2
        self.slots_per_row = 4
        
    def get_all_companions(self):
        # 開発中はすべての仲間を無制限に使用可能
        companions = []
        for companion_type in CompanionType:
            companions.append(Companion(companion_type))
        return companions
    
    def get_slot_rect(self, slot_index):
        """スロットの座標を取得"""
        row = slot_index // self.slots_per_row
        col = slot_index % self.slots_per_row
        x = 20 + col * (self.slot_width + 2)
        y = 30 + row * (self.slot_height + 2)
        return (x, y, self.slot_width, self.slot_height)
    
    def get_available_rect(self, comp_index):
        """利用可能な仲間リストの座標を取得"""
        row = comp_index // 3
        col = comp_index % 3
        x = 20 + col * (self.slot_width + 2)
        y = 70 + row * (self.slot_height + 2)
        return (x, y, self.slot_width, self.slot_height)
    
    def point_in_rect(self, point, rect):
        return (rect[0] <= point.x <= rect[0] + rect[2] and
                rect[1] <= point.y <= rect[1] + rect[3])
    
    def update(self, player):
        mouse_x, mouse_y = pyxel.mouse_x, pyxel.mouse_y
        mouse_pos = Vec2(mouse_x, mouse_y)
        
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            # ドラッグ開始
            self.dragging = None
            
            # スロットからのドラッグ
            for i, companion in enumerate(self.companion_slots):
                if companion and self.point_in_rect(mouse_pos, self.get_slot_rect(i)):
                    self.dragging = ('slot', i)
                    rect = self.get_slot_rect(i)
                    self.drag_offset = Vec2(mouse_x - rect[0], mouse_y - rect[1])
                    break
            
            # 利用可能な仲間からのドラッグ
            if not self.dragging:
                for i, companion in enumerate(self.available_companions):
                    if self.point_in_rect(mouse_pos, self.get_available_rect(i)):
                        self.dragging = ('available', i)
                        rect = self.get_available_rect(i)
                        self.drag_offset = Vec2(mouse_x - rect[0], mouse_y - rect[1])
                        break
        
        elif pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT) and self.dragging:
            # ドロップ処理
            drop_slot = None
            for i in range(len(self.companion_slots)):
                if self.point_in_rect(mouse_pos, self.get_slot_rect(i)):
                    drop_slot = i
                    break
            
            if drop_slot is not None:
                if self.dragging[0] == 'slot':
                    # スロット間の移動
                    source_slot = self.dragging[1]
                    companion = self.companion_slots[source_slot]
                    self.companion_slots[source_slot] = None
                    self.companion_slots[drop_slot] = companion
                elif self.dragging[0] == 'available':
                    # 利用可能な仲間をスロットに配置
                    companion_index = self.dragging[1]
                    companion_type = self.available_companions[companion_index].type
                    self.companion_slots[drop_slot] = Companion(companion_type)
            
            self.dragging = None
        
        # 右クリックでスロットから削除
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            for i in range(len(self.companion_slots)):
                if self.point_in_rect(mouse_pos, self.get_slot_rect(i)):
                    self.companion_slots[i] = None
                    break
        
        # プレイヤーの仲間リストを更新
        player.companions = [comp for comp in self.companion_slots if comp is not None]
        if not player.companions:  # 空の場合は基本攻撃を追加
            player.companions = [Companion(CompanionType.BASIC_SHOT)]
    
    def draw(self):
        # 仲間スロット描画
        pyxel.text(20, 20, "Companions:", 7)
        for i in range(len(self.companion_slots)):
            rect = self.get_slot_rect(i)
            pyxel.rect(rect[0], rect[1], rect[2], rect[3], 7)
            pyxel.rectb(rect[0], rect[1], rect[2], rect[3], 0)
            
            companion = self.companion_slots[i]
            if companion and (not self.dragging or self.dragging != ('slot', i)):
                # 仲間のアイコン（簡易表示）
                color = self.get_companion_color(companion.type)
                pyxel.rect(rect[0] + 1, rect[1] + 1, rect[2] - 2, rect[3] - 2, color)
        
        # 利用可能な仲間リスト描画
        pyxel.text(20, 60, "Available:", 7)
        for i, companion in enumerate(self.available_companions):
            rect = self.get_available_rect(i)
            color = self.get_companion_color(companion.type)
            
            if not self.dragging or self.dragging != ('available', i):
                pyxel.rect(rect[0], rect[1], rect[2], rect[3], color)
                pyxel.rectb(rect[0], rect[1], rect[2], rect[3], 0)
        
        # ドラッグ中のアイテム描画
        if self.dragging:
            mouse_x, mouse_y = pyxel.mouse_x, pyxel.mouse_y
            draw_x = mouse_x - self.drag_offset.x
            draw_y = mouse_y - self.drag_offset.y
            
            if self.dragging[0] == 'slot':
                companion = self.companion_slots[self.dragging[1]]
            else:
                companion = self.available_companions[self.dragging[1]]
            
            if companion:
                color = self.get_companion_color(companion.type)
                pyxel.rect(draw_x, draw_y, self.slot_width, self.slot_height, color)
                pyxel.rectb(draw_x, draw_y, self.slot_width, self.slot_height, 0)
        
        # 操作説明
        pyxel.text(90, 30, "Drag & Drop to equip", 7)
        pyxel.text(90, 40, "Right click to remove", 7)
        pyxel.text(90, 50, "P: Resume game", 7)
        
        # 現在装備中の仲間名表示
        y_offset = 100
        pyxel.text(20, y_offset, "Equipped:", 7)
        equipped = [comp for comp in self.companion_slots if comp is not None]
        for i, companion in enumerate(equipped):
            if y_offset + 10 + i * 8 < SCREEN_HEIGHT - 10:
                pyxel.text(20, y_offset + 10 + i * 8, companion.name, 6)
    
    def get_companion_color(self, companion_type):
        """仲間タイプに応じた色を返す"""
        colors = {
            CompanionType.BASIC_SHOT: 9,    # オレンジ
            CompanionType.RAPID_SHOT: 8,    # 赤
            CompanionType.SPREAD_SHOT: 11,  # 水色
            CompanionType.MULTICAST: 10,    # 黄色
            CompanionType.POWER_UP: 12,     # 紫
            CompanionType.HOMING: 3         # 緑
        }
        return colors.get(companion_type, 7)


class PauseScene(Scene):
    def __init__(self, game, game_scene):
        self.game = game
        self.game_scene = game_scene
        self.companion_editor = CompanionEditor()
        # 現在の仲間構成をエディターに読み込み
        self.load_current_companions()
        # マウスカーソルを表示
        pyxel.mouse(True)
    
    def load_current_companions(self):
        """現在プレイヤーが持っている仲間をエディターに読み込み"""
        for i, companion in enumerate(self.game_scene.player.companions[:8]):
            self.companion_editor.companion_slots[i] = companion
    
    def update(self):
        if pyxel.btnp(pyxel.KEY_P) or pyxel.btnp(pyxel.KEY_ESCAPE):
            # ゲーム再開時にマウスカーソルを非表示
            pyxel.mouse(False)
            self.game.change_scene(GameState.GAME)
            return
        
        # 仲間エディターの更新
        self.companion_editor.update(self.game_scene.player)
    
    def draw(self):
        # ゲーム画面を暗く描画
        self.game_scene.draw()
        pyxel.rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 1)  # 半透明の代わりに青
        
        # 仲間エディター描画
        self.companion_editor.draw()


class GameOverScene(Scene):
    def __init__(self, game):
        self.game = game
    
    def update(self):
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
            self.game.change_scene(GameState.TITLE)
    
    def draw(self):
        pyxel.cls(0)
        pyxel.text(45, 60, "GAME OVER", 8)
        pyxel.text(25, 80, "Press SPACE to Title", 7)


class ClearScene(Scene):
    def __init__(self, game):
        self.game = game
    
    def update(self):
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
            self.game.change_scene(GameState.TITLE)
    
    def draw(self):
        pyxel.cls(0)
        pyxel.text(50, 60, "CLEAR!", 11)
        pyxel.text(30, 80, "You Survived!", 7)
        pyxel.text(25, 100, "Press SPACE to Title", 7)


class Game:
    def __init__(self):
        self.state = GameState.TITLE
        self.scenes = {}
        self.current_scene = None
        
    def change_scene(self, new_state):
        self.state = new_state
        
        if new_state == GameState.TITLE:
            # タイトル画面ではマウスカーソルを非表示
            pyxel.mouse(False)
            self.current_scene = TitleScene(self)
            # ゲーム再開時にゲームシーンをリセット
            if GameState.GAME in self.scenes:
                del self.scenes[GameState.GAME]
        elif new_state == GameState.GAME:
            # ゲーム画面ではマウスカーソルを非表示
            pyxel.mouse(False)
            if new_state not in self.scenes:
                self.scenes[new_state] = GameScene(self)
            self.current_scene = self.scenes[new_state]
        elif new_state == GameState.LEVEL_UP:
            # レベルアップ画面ではマウスカーソルを非表示
            pyxel.mouse(False)
            self.current_scene = LevelUpScene(self, self.scenes[GameState.GAME])
        elif new_state == GameState.PAUSE:
            # ポーズ画面ではマウスカーソルを表示（PauseSceneのコンストラクタで設定）
            self.current_scene = PauseScene(self, self.scenes[GameState.GAME])
        elif new_state == GameState.GAME_OVER:
            # ゲームオーバー画面ではマウスカーソルを非表示
            pyxel.mouse(False)
            self.current_scene = GameOverScene(self)
        elif new_state == GameState.CLEAR:
            # クリア画面ではマウスカーソルを非表示
            pyxel.mouse(False)
            self.current_scene = ClearScene(self)
    
    def run(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="NOISAVA")
        pyxel.load("noisava.pyxres")
        
        # 初期状態でマウスカーソルを非表示
        pyxel.mouse(False)
        
        self.change_scene(GameState.TITLE)
        
        pyxel.run(self.update, self.draw)
    
    def update(self):
        if self.current_scene:
            self.current_scene.update()
    
    def draw(self):
        if self.current_scene:
            self.current_scene.draw()


if __name__ == "__main__":
    game = Game()
    game.run()
