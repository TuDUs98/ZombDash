import pygame
import random
import sys

pygame.init()

size = width, height = 1000, 600
screen = pygame.display.set_mode(size)
flag_of_run = True
FPS = 60


class Block(pygame.sprite.Sprite):
    def __init__(self, image, cords, width, height, size):
        pygame.sprite.Sprite.__init__(self)
        self.width = width
        self.height = height
        self.size = size
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = cords[0] + width * self.size
        self.rect.y = cords[1] + height * self.size


class Board(pygame.sprite.Group):
    def __init__(self, screen, imges, width, height, size, color, color_walls, file):
        # ширина и высота в "клеточках", и размеры клеточки в пикселях
        pygame.sprite.Group.__init__(self)
        self.width = width
        self.height = height
        self.size = size
        self.file = open(file)
        self.color = color
        self.images = imges
        self.screen = screen
        self.group = pygame.sprite.Group()
        self.color_walls = color_walls
        self.board = [list(s.rstrip('\n')) for s in self.file]

        # значения по умолчанию
        self.cords = 10, 10  # координаты верхнего левого угла

    def draw(self, surface):
        self.group.draw(self.screen)

    def update(self, *args):
        self.group.update(args)

    def set_view(self, cords, size):
        self.cords = cords
        self.size = size

    def render(self):  # отрисовка
        for h in range(len(self.board)):
            for w in range(len(self.board[h])):
                if self.board[h][w] == '0':
                    block = Block(self.images[0], self.cords, w, h, self.size)
                elif self.board[h][w] == '1':
                    block = Block(self.images[1], self.cords, w, h, self.size)

                self.group.add(block)

    def get_block_type(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.board[y][x]
        return None

    def get_size(self):
        return self.size

    def get_width_and_height(self):
        return self.width * self.size[0], self.height * self.size[1]

    def get_coords(self):
        return self.cords


class Player(pygame.sprite.Sprite):
    def __init__(self, board, cords, size, images, colorkey=None, color=None):  # images - left, right
        # указываются в клеточках, size - кортеж
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.board = board
        self.cords = cords
        if images is None:
            self.image = pygame.Surface((self.size[0] * self.board.get_size(), self.size[1] * self.board.get_size()))
            self.image.fill(color)
            if colorkey is not None:
                self.image.set_colorkey(colorkey)
        else:
            self.image_left = images[0]
            self.image_right = images[1]
            self.image_up = images[2]
            self.image_down = images[3]
            self.image = self.image_left
            if colorkey is not None:
                self.image_up.set_colorkey(colorkey)
                self.image_down.set_colorkey(colorkey)
                self.image_left.set_colorkey(colorkey)
                self.image_right.set_colorkey(colorkey)
        self.rect = self.image.get_rect()
        self.rect.x = self.board.get_coords()[0] + self.cords[0] * self.board.get_size()
        self.rect.y = self.board.get_coords()[1] + self.cords[1] * self.board.get_size()
        self.flag_of_run = []
        self.lost_direction = 'up'

    def move(self, x, y):
        self.rect = self.rect.move(x * self.board.get_size(), y * self.board.get_size())
        self.cords = self.cords[0] + x, self.cords[1] + y

    def get_flag_of_run(self):
        return self.flag_of_run

    def change_flag_of_run(self, new_value):
        self.flag_of_run = new_value

    def append_flag_of_run(self, value):
        self.flag_of_run.append(value)

    def delete_direction_in_flag_of_run(self, value):
        self.flag_of_run.pop(self.flag_of_run.index(value))

    def get_cords(self):
        return self.cords

    def get_size(self):
        return self.size

    def get_lost_direction(self):
        return self.lost_direction

    def change_lost_direction(self, direction):
        self.lost_direction = direction

    def change_image_left(self):
        self.image = self.image_left

    def change_image_right(self):
        self.image = self.image_right

    def change_image_up(self):
        self.image = self.image_up

    def change_image_down(self):
        self.image = self.image_down


class Bullet(pygame.sprite.Sprite):
    def __init__(self, board, image, cords, size, direction, speed):
        # direction - строка, size, cords, speed - 'в клеточках'
        pygame.sprite.Sprite.__init__(self)
        self.direction = direction
        self.size = size
        self.speed = speed
        self.board = board
        self.cords = cords
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = self.board.get_coords()[0] + self.cords[0] * self.board.get_size()
        self.rect.y = self.board.get_coords()[1] + self.cords[1] * self.board.get_size()

    def move(self):
        if self.direction == 'up':
            self.rect = self.rect.move(0, -(self.board.get_size()))
            self.cords = self.cords[0], self.cords[1] - 1
        elif self.direction == 'down':
            self.rect = self.rect.move(0, self.board.get_size())
            self.cords = self.cords[0], self.cords[1] + 1
        elif self.direction == 'right':
            self.rect = self.rect.move(self.board.get_size(), 0)
            self.cords = self.cords[0] + 1, self.cords[1]
        elif self.direction == 'left':
            self.rect = self.rect.move(-self.board.get_size(), 0)
            self.cords = self.cords[0] - 1, self.cords[1]

    def get_cords(self):
        return self.cords

    def get_direction(self):
        return self.direction

    def get_speed(self):
        return self.speed


class Enemy(pygame.sprite.Sprite):
    def __init__(self, board, images, cords, size, speed, hp, flag_of_moves=True):  # в "кубиках", images - left, right
        pygame.sprite.Sprite.__init__(self)
        self.board = board
        self.len = 0
        self.flag_of_move = False
        self.cords = cords
        self.size = size
        self.speed = speed
        self.hp = hp
        self.flag_of_moves = flag_of_moves
        self.image_left = images[0]
        self.image_right = images[1]
        self.image = self.image_left
        self.rect = self.image.get_rect()
        self.rect.x = self.board.get_coords()[0] + self.cords[0] * self.board.get_size()
        self.rect.y = self.board.get_coords()[1] + self.cords[1] * self.board.get_size()
        self.direction = None

    def move(self):
        if self.flag_of_moves:
            if self.len > 0:
                if self.direction == 'up':
                    self.image = random.choice([self.image_left, self.image_right])
                    self.rect = self.rect.move(0, -(self.board.get_size()))
                    self.cords = self.cords[0], self.cords[1] - 1
                elif self.direction == 'down':
                    self.image = random.choice([self.image_left, self.image_right])
                    self.rect = self.rect.move(0, self.board.get_size())
                    self.cords = self.cords[0], self.cords[1] + 1
                elif self.direction == 'right':
                    self.image = self.image_right
                    self.rect = self.rect.move(self.board.get_size(), 0)
                    self.cords = self.cords[0] + 1, self.cords[1]
                elif self.direction == 'left':
                    self.image = self.image_left
                    self.rect = self.rect.move(-self.board.get_size(), 0)
                    self.cords = self.cords[0] - 1, self.cords[1]
                self.len -= 1
            else:
                self.flag_of_move = False

    def get_cords(self):
        return self.cords

    def change_direction(self, direction):
        self.direction = direction

    def change_len(self, len):
        self.len = len

    def get_size(self):
        return self.size

    def get_speed(self):
        return self.speed

    def get_flag_of_move(self):
        return self.flag_of_move

    def change_flag_of_move(self):
        self.flag_of_move = not self.flag_of_move

    def get_direction(self):
        return self.direction

    def get_hp(self):
        return self.hp

    def reduce_hp(self):
        self.hp -= 1


def terminate():
    pygame.quit()
    sys.exit()


def creators_screen(difficulty):
    intro_text = ["Автор игры:",
                  "   Исмаиловв назар",
                  "Автор идеи:",
                  "   Яшин Илья",
                  "Альфа-тестеры:",
                  "   Сидоров Павел",
                  "Бетта-тестеры:",
                  "   Сидоров Павел",
                  "   Лазарев Никита",
                  "",
                  "     <назад>"]

    fon = pygame.transform.scale(pygame.image.load('data/Sprites/fon_6.jpg'), (width, height))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 40)
    text_coord = 10
    list_of_texts = []
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 20
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        list_of_texts.append(intro_rect)
        screen.blit(string_rendered, intro_rect)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for i in range(len(list_of_texts)):
                        rec = list_of_texts[i]
                        if rec.x <= event.pos[0] <= rec.x + rec.width and rec.y <= event.pos[1] \
                                <= rec.y + rec.height:
                            if i == 10:
                                start_screen(difficulty)
                                return
            if event.type == pygame.QUIT:
                terminate()
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)


def roots_screen(difficulty):
    intro_text = ["ПРАВИЛА:",
                  "1) ваша цель прожить как можно дольше! ",
                  "2) убивайте зомби, за это вам дают доп очки",
                  "    НО! чем больше вы их убьёте,",
                  "    тем больше их будет",
                  "3) если они вас коснутся, вы умрёте... ",
                  "УПРАВЛЕНИЕ:",
                  "w, a, s, d - управление перемещением персонажа",
                  "Space - стрельба",
                  "",
                  "     <назад>"]

    fon = pygame.transform.scale(pygame.image.load('data/Sprites/fon_6.jpg'), (width, height))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 32)
    text_coord = 10
    list_of_texts = []
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 20
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        list_of_texts.append(intro_rect)
        screen.blit(string_rendered, intro_rect)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for i in range(len(list_of_texts)):
                        rec = list_of_texts[i]
                        if rec.x <= event.pos[0] <= rec.x + rec.width and rec.y <= event.pos[1] \
                                <= rec.y + rec.height:
                            if i == 10:
                                start_screen(difficulty)
                                return
            if event.type == pygame.QUIT:
                terminate()
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)


def start_screen(difficulty):
    record_file = open('data/records.txt')
    record = int(record_file.readline().rstrip('\n'))

    intro_text = ["<играть>",
                  "<правила>",
                  "<создатели>",
                  f"сложность: {difficulty}",
                  "лучший рекорд:",
                  f" <{record}>"]

    fon = pygame.transform.scale(pygame.image.load('data/Sprites/fon_6.jpg'), (width, height))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 60)
    text_coord = 10
    list_of_texts = []
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 20
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        list_of_texts.append(intro_rect)
        screen.blit(string_rendered, intro_rect)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for i in range(len(list_of_texts)):
                        rec = list_of_texts[i]
                        if rec.x <= event.pos[0] <= rec.x + rec.width and rec.y <= event.pos[1] <= rec.y + rec.height:
                            if i == 0:
                                game(difficulty)
                                return difficulty
                            elif i == 1:
                                roots_screen(difficulty)
                                return
                            elif i == 2:
                                creators_screen(difficulty)
                                return
                            elif i == 3:
                                if difficulty == 'легко':
                                    difficulty = 'нормально'
                                    start_screen(difficulty)
                                    return difficulty
                                elif difficulty == 'нормально':
                                    difficulty = 'сложно'
                                    start_screen(difficulty)
                                    return difficulty
                                elif difficulty == 'сложно':
                                    difficulty = 'легко'
                                    start_screen(difficulty)
                                    return difficulty

            if event.type == pygame.QUIT:
                terminate()
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)


def pause_screen(difficulty):
    intro_text = ["<продолжить>",
                  "<заново>",
                  "<главное меню>"]

    fon = pygame.transform.scale(pygame.image.load('data/Sprites/fon_6.jpg'), (width, height))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 60)
    text_coord = 10
    list_of_texts = []
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 20
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        list_of_texts.append(intro_rect)
        screen.blit(string_rendered, intro_rect)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for i in range(len(list_of_texts)):
                        rec = list_of_texts[i]
                        if rec.x <= event.pos[0] <= rec.x + rec.width and rec.y <= event.pos[1] <= rec.y + rec.height:
                            if i == 0:
                                return
                            elif i == 1:
                                game(difficulty)
                                return
                            elif i == 2:
                                start_screen(difficulty)
                                return

            if event.type == pygame.QUIT:
                terminate()
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)


def end_screen(score, flag_of_record, difficulty):
    if score == -1:
        intro_text = ['']
        fon = pygame.transform.scale(pygame.image.load('data/Sprites/die_fon.jpg'), (width, height))
    elif score == 73:
        intro_text = ["ВЫ ПРОИГРАЛИ!(((",
                      "добро пожаловать в ульяновск",
                      f"ВАШ СЧЕТ: {score}",
                      "<заново>",
                      "<вернуться в главное меню>",
                      "",
                      "<выйти из города>"]
        fon = pygame.transform.scale(pygame.image.load('data/Sprites/lenin.png'), (width, height))
    elif flag_of_record:
        intro_text = ["ВЫ ПРОИГРАЛИ!(((",
                      "!!!НОВЫЙ РЕКОРД!!!",
                      f"ВАШ СЧЕТ: {score}",
                      "<заново>",
                      "<вернуться в главное меню>",
                      "",
                      "<выйти>"]
        fon = pygame.transform.scale(pygame.image.load('data/Sprites/fon_6.jpg'), (width, height))
    else:
        intro_text = ["ВЫ ПРОИГРАЛИ!(((",
                      "!!!неНОВЫЙ РЕКОРД!!!",
                      f"ВАШ СЧЕТ: {score}",
                      "<заново>",
                      "<вернуться в главное меню>",
                      "",
                      "<выйти>"]
        fon = pygame.transform.scale(pygame.image.load('data/Sprites/fon_6.jpg'), (width, height))

    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 60)
    text_coord = 10
    list_of_texts = []
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 20
        intro_rect.top = text_coord
        intro_rect.x = 10
        text_coord += intro_rect.height
        list_of_texts.append(intro_rect)
        screen.blit(string_rendered, intro_rect)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for i in range(len(list_of_texts)):
                        rec = list_of_texts[i]
                        if rec.x <= event.pos[0] <= rec.x + rec.width and rec.y <= event.pos[1] <= rec.y + rec.height:
                            if i == 3:
                                game(difficulty)
                                return
                            elif i == 4:
                                start_screen(difficulty)
                                return
                            elif i == 6:
                                terminate()
            if event.type == pygame.QUIT:
                terminate()
        pygame.display.flip()
        pygame.time.Clock().tick(FPS)


def game(difficulty):
    global flag_of_run

    score = 0
    score_flag = 0
    all_sprites = pygame.sprite.Group()
    bullets_group = pygame.sprite.Group()
    all_enemies = pygame.sprite.Group()
    count_of_zombies_killed = 0
    count_of_zombies = 1
    flag_of_cheater = False
    board = Board(screen, [pygame.image.load('data/Sprites/ground_1.jpg'),
                           pygame.image.load('data/Sprites/wall_1.jpg')],
                  70, 65, 9, (50, 50, 50), (150, 75, 0), 'data/Levels/map.txt')
    board.render()
    player_shield = Player(board, (47, 42), (30, 30), None, (0, 0, 0), (0, 0, 0))
    player = Player(board, (64, 59), (5, 5), [pygame.image.load('data/Sprites/player_1_left.png'),
                                              pygame.image.load('data/Sprites/player_1_right.png'),
                                              pygame.image.load('data/Sprites/player_1_up.png').convert(),
                                              pygame.image.load('data/Sprites/player_1_down.png').convert()],
                    pygame.Color('white'))
    all_sprites.add(player_shield)
    all_sprites.add(player)
    BULLETEVENT = 31
    ENEMYEVENT = 30
    SCOREEVENT = 29
    ENEMYSPAWNEVENT = 28
    if difficulty == 'легко':
        time_of_spawn = 6500
    elif difficulty == 'нормально':
        time_of_spawn = 4500
    elif difficulty == 'сложно':
        time_of_spawn = 2500
    bullet_tic = pygame.time.set_timer(BULLETEVENT, 10)
    enemy_tic = pygame.time.set_timer(ENEMYEVENT, 20)
    score_tic = pygame.time.set_timer(SCOREEVENT, 1000)
    enemyspawn_tic = pygame.time.set_timer(ENEMYSPAWNEVENT, time_of_spawn)

    while flag_of_run:

        screen.fill((0, 0, 0))

        board.draw(screen)

        font = pygame.font.Font(None, 50)
        text = font.render(f"СЧЁТ: {score}", 1, (100, 255, 100))
        text_x = width - text.get_width() - 20
        text_y = text.get_height()
        text_w = text.get_width()
        text_h = text.get_height()
        screen.blit(text, (text_x, text_y))
        pygame.draw.rect(screen, (0, 255, 0), (text_x - 10, text_y - 10,
                                               text_w + 20, text_h + 20), 1)

        font = pygame.font.Font(None, 50)
        text = font.render(f"УБИТО ЗОМБИ: {count_of_zombies_killed}", 1, (100, 255, 100))
        text_x = width - text.get_width() - 20
        text_y = text.get_height() + 80
        text_w = text.get_width()
        text_h = text.get_height()
        screen.blit(text, (text_x, text_y))
        pygame.draw.rect(screen, (0, 255, 0), (text_x - 10, text_y - 10,
                                               text_w + 20, text_h + 20), 1)

        for direction in player.get_flag_of_run():
            if direction == 'left':
                player.change_image_left()
                lst = [board.get_block_type(player.get_cords()[0] - 1,
                                            player.get_cords()[1] + i) == '0' for i in range(player.get_size()[1])]
                if all(lst):
                    player.change_lost_direction('left')
                    player.move(-1, 0)
                    player_shield.move(-1, 0)
            elif direction == 'right':
                player.change_image_right()
                lst = [board.get_block_type(player.get_cords()[0] + player.get_size()[0],
                                            player.get_cords()[1] + i) == '0'
                       for i in range(player.get_size()[1])]
                if all(lst):
                    player.change_lost_direction('right')
                    player.move(1, 0)
                    player_shield.move(1, 0)
            elif direction == 'down':
                player.change_image_down()
                lst = [board.get_block_type(player.get_cords()[0] + i,
                                            player.get_cords()[1] + player.get_size()[1]) == '0'
                       for i in range(player.get_size()[1])]
                if all(lst):
                    player.change_lost_direction('down')
                    player.move(0, 1)
                    player_shield.move(0, 1)
            elif direction == 'up':
                player.change_image_up()
                lst = [board.get_block_type(player.get_cords()[0] + i,
                                            player.get_cords()[1] - 1) == '0'
                       for i in range(player.get_size()[1])]
                if all(lst):
                    player.change_lost_direction('up')
                    player.move(0, -1)
                    player_shield.move(0, -1)

        for event in pygame.event.get():
            if event.type == ENEMYSPAWNEVENT:
                if score_flag >= 50 and time_of_spawn >= 2000:
                    time_of_spawn -= 250
                    enemyspawn_tic = pygame.time.set_timer(ENEMYSPAWNEVENT, time_of_spawn)
                    score_flag = 0
                flag_of_spawn = False
                while not flag_of_spawn:
                    x = random.randint(0, 66)
                    y = random.randint(0, 61)
                    if count_of_zombies % 20 == 0:
                        sprites_of_enemy = [pygame.image.load('data/Sprites/zombie_5_left.png'),
                                            pygame.image.load('data/Sprites/zombie_5_right.png')]
                        enemy = Enemy(board, sprites_of_enemy, (x, y), (15, 15), 1, 30)
                    elif count_of_zombies % 10 == 0:
                        sprites_of_enemy = [pygame.image.load('data/Sprites/zombie_6_left.png'),
                                            pygame.image.load('data/Sprites/zombie_6_right.png')]
                        enemy = Enemy(board, sprites_of_enemy, (x, y), (5, 5), 3, 2)
                    elif count_of_zombies % 5 == 0:
                        flag_of_enemy = random.randint(1, 2)
                        if flag_of_enemy == 2:
                            sprites_of_enemy = [pygame.image.load('data/Sprites/zombie_3_left.png'),
                                                pygame.image.load('data/Sprites/zombie_3_right.png')]
                            enemy = Enemy(board, sprites_of_enemy, (x, y), (5, 5), 1, 2)
                        elif flag_of_enemy == 1:
                            sprites_of_enemy = [pygame.image.load('data/Sprites/zombie_4_left.png'),
                                                pygame.image.load('data/Sprites/zombie_4_right.png')]
                            enemy = Enemy(board, sprites_of_enemy, (x, y), (5, 5), 1, 10, False)
                    else:
                        sprites_of_enemy = random.choice([[pygame.image.load('data/Sprites/zombie_1_left.png'),
                                                           pygame.image.load('data/Sprites/zombie_1_right.png')],
                                                          [pygame.image.load('data/Sprites/zombie_2_left.png'),
                                                           pygame.image.load('data/Sprites/zombie_2_right.png')]])
                        enemy = Enemy(board, sprites_of_enemy, (x, y), (5, 5), 1, 1)
                    flag = True
                    if len(all_enemies) < 1000:
                            lst = [board.get_block_type(enemy.get_cords()[0] + i,
                                                        enemy.get_cords()[1] + j) == '0'
                                   for i in range(enemy.get_size()[0]) for j in range(enemy.get_size()[1])]
                            if not pygame.sprite.collide_rect(player_shield, enemy) and all(lst):
                                all_sprites.add(enemy)
                                all_enemies.add(enemy)
                                flag_of_spawn = True
                                count_of_zombies += 1
                    else:
                        flag_of_spawn = False
            if event.type == SCOREEVENT:
                score += 1
                score_flag += 1
            if event.type == ENEMYEVENT:
                for enemy in all_enemies:
                    if enemy.get_flag_of_move():
                        for _ in range(enemy.get_speed()):
                            if enemy.get_flag_of_move():
                                if enemy.get_direction() == 'left':
                                    lst = [board.get_block_type(enemy.get_cords()[0] - 1,
                                                                enemy.get_cords()[1] + i) == '0' for i in
                                           range(enemy.get_size()[1])]
                                elif enemy.get_direction() == 'right':
                                    lst = [board.get_block_type(enemy.get_cords()[0] + enemy.get_size()[0],
                                                                enemy.get_cords()[1] + i) == '0'
                                           for i in range(enemy.get_size()[1])]
                                elif enemy.get_direction() == 'down':
                                    lst = [board.get_block_type(enemy.get_cords()[0] + i,
                                                                enemy.get_cords()[1] + enemy.get_size()[1]) == '0'
                                           for i in range(enemy.get_size()[0])]
                                elif enemy.get_direction() == 'up':
                                    lst = [board.get_block_type(enemy.get_cords()[0] + i,
                                                                enemy.get_cords()[1] - 1) == '0'
                                           for i in range(enemy.get_size()[0])]
                                if all(lst):
                                    enemy.move()
                                    if pygame.sprite.collide_rect(enemy, player):
                                        if not flag_of_cheater:
                                            record_file = open('data/records.txt')
                                            record = int(record_file.readline().rstrip('\n'))
                                            if score > record:
                                                record_file.close()
                                                record_file = open('data/records.txt', 'w')
                                                print(score, file=record_file)
                                                record_file.close()
                                                end_screen(score, True, difficulty)
                                            else:
                                                end_screen(score, False, difficulty)
                                            flag_of_run = False
                                else:
                                    enemy.change_flag_of_move()
                    else:
                        enemy.change_direction(random.choice(['left', 'right', 'up', 'down']))
                        enemy.change_len(random.randint(10, 25))
                        enemy.change_flag_of_move()

            if event.type == BULLETEVENT:
                for bul in bullets_group:
                    for enemy in all_enemies:
                        if pygame.sprite.collide_rect(enemy, bul):
                            enemy.reduce_hp()
                            if enemy.get_hp() == 0:
                                enemy.kill()
                                count_of_zombies_killed += 1
                            bul.kill()
                            score += 10
                            score_flag += 10
                    if bul.get_direction() == 'left':
                        if board.get_block_type(bul.get_cords()[0] - 1, bul.get_cords()[1]) == '0':
                            bul.move()
                        else:
                            bul.kill()
                    if bul.get_direction() == 'right':
                        if board.get_block_type(bul.get_cords()[0] + 1, bul.get_cords()[1]) == '0':
                            bul.move()
                        else:
                            bul.kill()
                    if bul.get_direction() == 'up':
                        if board.get_block_type(bul.get_cords()[0], bul.get_cords()[1] - 1) == '0':
                            bul.move()
                        else:
                            bul.kill()
                    if bul.get_direction() == 'down':
                        if board.get_block_type(bul.get_cords()[0], bul.get_cords()[1] + 1) == '0':
                            bul.move()
                        else:
                            bul.kill()
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    pause_screen(difficulty)

                if event.key == pygame.K_a:
                    player.append_flag_of_run('left')
                    player.change_lost_direction('left')
                elif event.key == pygame.K_d:
                    player.append_flag_of_run('right')
                    player.change_lost_direction('right')
                elif event.key == pygame.K_s:
                    player.append_flag_of_run('down')
                    player.change_lost_direction('down')
                elif event.key == pygame.K_w:
                    player.append_flag_of_run('up')
                    player.change_lost_direction('up')

                elif event.key == pygame.K_SPACE:
                    if player.get_lost_direction() == 'up':
                        bullet = Bullet(board, pygame.image.load('data/Sprites/bullet_1_up.png'),
                                        (player.get_cords()[0] + 2, player.get_cords()[1] + 2),
                                        (1, 1), player.get_lost_direction(), 3)
                    elif player.get_lost_direction() == 'down':
                        bullet = Bullet(board, pygame.image.load('data/Sprites/bullet_1_down.png'),
                                        (player.get_cords()[0] + 2, player.get_cords()[1] + 2),
                                        (1, 1), player.get_lost_direction(), 3)
                    elif player.get_lost_direction() == 'left':
                        bullet = Bullet(board, pygame.image.load('data/Sprites/bullet_1_left.png'),
                                        (player.get_cords()[0] + 2, player.get_cords()[1] + 2),
                                        (1, 1), player.get_lost_direction(), 3)
                    if player.get_lost_direction() == 'right':
                        bullet = Bullet(board, pygame.image.load('data/Sprites/bullet_1_right.png'),
                                        (player.get_cords()[0] + 2, player.get_cords()[1] + 2),
                                        (1, 1), player.get_lost_direction(), 3)
                    all_sprites.add(bullet)
                    bullets_group.add(bullet)

                keys = pygame.key.get_pressed()
                # клавиши для введения чит-кодов зажимать
                if keys[pygame.K_l] and keys[pygame.K_m] and keys[pygame.K_s]:  # чит-код от дяди Лёни на бессмертие
                    flag_of_cheater = not flag_of_cheater

                elif keys[pygame.K_t] and keys[pygame.K_a] and keys[pygame.K_n] and keys[pygame.K_o]\
                        and keys[pygame.K_s]:  # чит-код на смерть всех мобов
                    for enemy in all_enemies:
                        count_of_zombies_killed += 1
                        enemy.kill()

                elif keys[pygame.K_k] and keys[pygame.K_o] and keys[pygame.K_p]:  # чит-код на очки
                    score_tic = pygame.time.set_timer(SCOREEVENT, 10)

                elif keys[pygame.K_z] and keys[pygame.K_x] and keys[pygame.K_c]:  # чит-код на мгновенную смерть
                    end_screen(-1, False, difficulty)
                    flag_of_run = False

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    player.delete_direction_in_flag_of_run('left')
                elif event.key == pygame.K_d:
                    player.delete_direction_in_flag_of_run('right')
                elif event.key == pygame.K_s:
                    player.delete_direction_in_flag_of_run('down')
                elif event.key == pygame.K_w:
                    player.delete_direction_in_flag_of_run('up')

            if event.type == pygame.QUIT:
                terminate()

        all_sprites.draw(screen)
        all_sprites.update()
        board.update()

        pygame.display.update()

        pygame.time.Clock().tick(FPS)
        pygame.event.pump()


start_screen('нормально')
