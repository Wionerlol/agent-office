import { Application, Container, Graphics, Text, TextStyle } from "pixi.js";

import { OFFICE_HEIGHT, OFFICE_WIDTH, POSITIONS, ZONES, type Point } from "./layout";

const COLORS = {
  ink: 0x263335,
  wall: 0x435052,
  wallTop: 0xf2ead9,
  wood: 0xb99167,
  woodDark: 0x76563e,
  metal: 0x56676a,
  screen: 0x203c48,
  chair: 0x486369,
  plant: 0x52745c,
  pot: 0xa86448,
};

function label(text: string, x: number, y: number, options: { size?: number; color?: number; weight?: "400" | "600" | "700"; anchor?: number } = {}): Text {
  const item = new Text({
    text,
    style: new TextStyle({
      fontFamily: "Inter, system-ui, sans-serif",
      fontSize: options.size ?? 11,
      fill: options.color ?? COLORS.ink,
      fontWeight: options.weight ?? "600",
      letterSpacing: 1.2,
    }),
  });
  item.anchor.set(options.anchor ?? 0);
  item.position.set(x, y);
  return item;
}

function drawFloor(scene: Container): void {
  scene.addChild(
    new Graphics()
      .roundRect(12, 12, OFFICE_WIDTH - 24, OFFICE_HEIGHT - 24, 20)
      .fill(0xd7c5a8),
  );
  const boards = new Graphics();
  for (let y = 28; y < OFFICE_HEIGHT - 28; y += 26) {
    boards.moveTo(24, y).lineTo(OFFICE_WIDTH - 24, y);
    const offset = Math.floor(y / 26) % 2 ? 54 : 0;
    for (let x = 24 + offset; x < OFFICE_WIDTH - 24; x += 108) {
      boards.moveTo(x, y - 26).lineTo(x, y);
    }
  }
  boards.stroke({ width: 1, color: 0x9e8265, alpha: 0.2 });
  scene.addChild(boards);
}

function drawRooms(scene: Container): void {
  for (const zone of ZONES) {
    scene.addChild(
      new Graphics()
        .rect(zone.x, zone.y, zone.width, zone.height)
        .fill({ color: zone.color, alpha: zone.id === "desk_area" ? 0.26 : 0.48 }),
    );
    scene.addChild(label(zone.label, zone.x + 12, zone.y + 10, { size: 10, color: 0x4a5756, weight: "700" }));
  }

  const walls = new Graphics();
  walls.roundRect(16, 16, OFFICE_WIDTH - 32, OFFICE_HEIGHT - 32, 16).stroke({ width: 10, color: COLORS.wall });
  walls.roundRect(22, 22, OFFICE_WIDTH - 44, OFFICE_HEIGHT - 44, 12).stroke({ width: 3, color: COLORS.wallTop });
  walls.moveTo(158, 28).lineTo(158, 165).moveTo(158, 215).lineTo(158, 260);
  walls.moveTo(158, 408).lineTo(158, 652);
  walls.moveTo(797, 28).lineTo(797, 165).moveTo(797, 215).lineTo(797, 226);
  walls.moveTo(804, 226).lineTo(900, 226).moveTo(950, 226).lineTo(1074, 226);
  walls.moveTo(820, 226).lineTo(820, 340).moveTo(820, 390).lineTo(820, 476);
  walls.moveTo(158, 444).lineTo(240, 444).moveTo(310, 444).lineTo(430, 444);
  walls.moveTo(500, 444).lineTo(650, 444).moveTo(720, 444).lineTo(820, 444);
  walls.stroke({ width: 7, color: COLORS.wall });
  scene.addChild(walls);

  const windows = new Graphics();
  for (const x of [226, 404, 582, 858]) {
    windows.roundRect(x, 17, 112, 12, 3).fill(0x91bed0).stroke({ width: 2, color: 0xe5f1ef });
    windows.moveTo(x + 56, 19).lineTo(x + 56, 27).stroke({ width: 1, color: 0xd4e7e8 });
  }
  scene.addChild(windows);

  const door = new Graphics();
  door.rect(1060, 536, 12, 92).fill(0x6e5140).rect(1050, 540, 10, 84).fill(0xb9d4cf);
  door.circle(1054, 584, 3).fill(0xd9b867);
  scene.addChild(door, label("EXIT", 1055, 524, { size: 9, color: 0x8b4139, anchor: 0.5 }));
}

function drawDesk(scene: Container, id: string, point: Point): void {
  const x = point.x;
  const y = point.y;
  const furniture = new Graphics();
  furniture.ellipse(x, y + 9, 31, 18).fill({ color: 0x243537, alpha: 0.18 });
  furniture.roundRect(x - 28, y - 2, 56, 37, 13).fill(COLORS.chair);
  furniture.roundRect(x - 57, y - 66, 114, 49, 6).fill(COLORS.woodDark);
  furniture.roundRect(x - 54, y - 64, 108, 42, 5).fill(COLORS.wood);
  furniture.rect(x - 4, y - 77, 8, 15).fill(COLORS.metal);
  furniture.roundRect(x - 31, y - 103, 62, 30, 4).fill(COLORS.ink);
  furniture.roundRect(x - 27, y - 99, 54, 22, 2).fill(COLORS.screen);
  furniture.rect(x - 22, y - 57, 44, 9).fill(0xddd6c7);
  furniture.circle(x + 41, y - 46, 5).fill(0x5d4938);
  scene.addChild(furniture, label(id.replace("desk-", "D"), x - 50, y - 57, { size: 8, color: 0xf7eddb }));
}

function drawOpenOffice(scene: Container): void {
  const whiteboard = new Graphics()
    .roundRect(205, 55, 170, 48, 4)
    .fill(0xf4f2e9)
    .stroke({ width: 3, color: 0x7c8987 });
  whiteboard.moveTo(223, 86).lineTo(275, 68).lineTo(324, 87).lineTo(352, 66).stroke({ width: 2, color: 0x5b8c86 });
  scene.addChild(whiteboard);

  Object.entries(POSITIONS)
    .filter(([id]) => id.startsWith("desk-"))
    .forEach(([id, point]) => drawDesk(scene, id, point));
}

function drawLibrary(scene: Container): void {
  const shelf = new Graphics();
  shelf.roundRect(834, 74, 204, 34, 3).fill(0x795a42);
  for (let x = 842; x < 1028; x += 13) {
    const colors = [0xa9574d, 0x567c73, 0xc1954c, 0x6e6386];
    shelf.rect(x, 79, 9, 23).fill(colors[Math.floor(x / 13) % colors.length]);
  }
  shelf.roundRect(892, 126, 100, 20, 8).fill(0xb28a62);
  shelf.circle(910, 150, 13).fill(0x657a76).circle(974, 150, 13).fill(0x657a76);
  scene.addChild(shelf);
}

function drawCoffeeArea(scene: Container): void {
  const coffee = new Graphics();
  coffee.roundRect(188, 485, 145, 39, 5).fill(0x8b684d);
  coffee.roundRect(203, 459, 48, 40, 5).fill(COLORS.metal);
  coffee.rect(211, 466, 31, 16).fill(0x263f47).circle(227, 488, 4).fill(0x3b2d28);
  coffee.roundRect(274, 475, 34, 24, 4).fill(0xbfd0ce).circle(302, 466, 8).fill(0x7e9a91);
  for (const x of [216, 287]) coffee.circle(x, 585, 19).fill(0x6d5241).rect(x - 3, 584, 6, 28).fill(0x5a4639);
  scene.addChild(coffee, label("COFFEE BAR", 260, 535, { size: 9, color: 0x675142, anchor: 0.5 }));
}

function drawLounge(scene: Container): void {
  const lounge = new Graphics();
  lounge.roundRect(400, 493, 158, 118, 16).fill({ color: 0xb48c72, alpha: 0.28 });
  lounge.roundRect(400, 493, 158, 42, 14).fill(0x69817d);
  lounge.roundRect(414, 500, 61, 27, 10).fill(0x78908b);
  lounge.roundRect(483, 500, 61, 27, 10).fill(0x78908b);
  lounge.ellipse(478, 603, 37, 11).fill({ color: 0x47352d, alpha: 0.16 });
  lounge.roundRect(442, 590, 73, 25, 12).fill(0xa37959);
  scene.addChild(lounge);
}

function drawToolLab(scene: Container): void {
  const lab = new Graphics();
  for (const x of [620, 676, 732]) {
    lab.roundRect(x, 482, 43, 68, 5).fill(0x44575a).stroke({ width: 2, color: 0x29383a });
    for (let y = 492; y < 540; y += 14) {
      lab.rect(x + 7, y, 29, 9).fill(0x253638);
      lab.circle(x + 13, y + 4, 2).fill(y % 28 ? 0x7fc98b : 0xe5b861);
    }
  }
  lab.roundRect(784, 510, 17, 79, 5).fill(0x7b654f);
  scene.addChild(lab, label("BUILD · SHELL · LINT", 705, 616, { size: 8, color: 0x4e5e5d, anchor: 0.5 }));
}

function drawTestLab(scene: Container): void {
  const lab = new Graphics();
  lab.roundRect(850, 274, 190, 60, 6).fill(0x74807a);
  for (const x of [866, 927, 988]) {
    lab.roundRect(x, 284, 46, 30, 3).fill(0x28383c);
    lab.roundRect(x + 4, 288, 38, 20, 2).fill(0x5b8f8b);
    lab.rect(x + 20, 314, 6, 10).fill(0x465557);
  }
  lab.roundRect(854, 418, 182, 28, 4).fill(0x9b8469);
  for (const x of [874, 918, 962, 1006]) lab.circle(x, 410, 7).fill(0xd8e0d9).stroke({ width: 2, color: 0x607c77 });
  scene.addChild(lab, label("TEST MATRIX", 945, 350, { size: 9, color: 0x52625d, anchor: 0.5 }));
}

function drawReception(scene: Container): void {
  const reception = new Graphics();
  reception.roundRect(42, 303, 88, 43, 8).fill(COLORS.woodDark);
  reception.roundRect(46, 300, 80, 36, 6).fill(COLORS.wood);
  reception.rect(80, 283, 30, 20).fill(COLORS.screen).rect(92, 303, 5, 9).fill(COLORS.metal);
  reception.roundRect(48, 362, 76, 16, 8).fill(0x6d837d);
  scene.addChild(reception, label("WELCOME", 84, 384, { size: 8, color: 0x52615e, anchor: 0.5 }));
}

function drawPlant(scene: Container, x: number, y: number, scale = 1): void {
  const plant = new Graphics();
  plant.roundRect(x - 12 * scale, y, 24 * scale, 20 * scale, 4).fill(COLORS.pot);
  plant.ellipse(x - 8 * scale, y - 12 * scale, 8 * scale, 18 * scale).fill(COLORS.plant);
  plant.ellipse(x + 8 * scale, y - 15 * scale, 8 * scale, 20 * scale).fill(0x648566);
  plant.ellipse(x, y - 24 * scale, 8 * scale, 21 * scale).fill(0x456a51);
  scene.addChild(plant);
}

function drawDetails(scene: Container): void {
  drawPlant(scene, 182, 410, 0.8);
  drawPlant(scene, 775, 414, 0.8);
  drawPlant(scene, 1042, 198, 0.75);
  drawPlant(scene, 1030, 620, 0.7);

  const clock = new Graphics().circle(778, 56, 15).fill(0xf3eee1).stroke({ width: 3, color: 0x4b5958 });
  clock.moveTo(778, 56).lineTo(778, 47).moveTo(778, 56).lineTo(786, 60).stroke({ width: 2, color: 0x4b5958 });
  scene.addChild(clock);
}

function drawLighting(scene: Container): void {
  const hour = new Date().getHours();
  if (hour < 7 || hour >= 19) {
    scene.addChild(
      new Graphics()
        .roundRect(22, 22, OFFICE_WIDTH - 44, OFFICE_HEIGHT - 44, 14)
        .fill({ color: 0x11243b, alpha: 0.2 }),
    );
    const lights = new Graphics();
    for (const [x, y] of [[320, 230], [620, 230], [930, 360], [480, 555]]) {
      lights.circle(x, y, 82).fill({ color: 0xffe5a4, alpha: 0.055 });
    }
    scene.addChild(lights);
  }
}

function drawForeground(scene: Container): void {
  const foreground = new Graphics();
  for (const point of Object.entries(POSITIONS)
    .filter(([id]) => id.startsWith("desk-"))
    .map(([, point]) => point)) {
    foreground.roundRect(point.x - 54, point.y - 29, 108, 12, 3).fill(0x76563e);
  }
  foreground.roundRect(46, 326, 80, 15, 4).fill(0x76563e);
  foreground.roundRect(188, 510, 145, 14, 3).fill(0x71513d);
  foreground.roundRect(400, 522, 158, 13, 5).fill(0x536b67);
  foreground.roundRect(442, 599, 73, 16, 8).fill(0x8e684e);
  foreground.roundRect(854, 430, 182, 16, 3).fill(0x806b55);
  scene.addChild(foreground);
}

export function drawOfficeScenery(app: Application): void {
  const background = new Container();
  background.zIndex = 0;
  drawFloor(background);
  drawRooms(background);
  drawOpenOffice(background);
  drawLibrary(background);
  drawCoffeeArea(background);
  drawLounge(background);
  drawToolLab(background);
  drawTestLab(background);
  drawReception(background);
  drawDetails(background);
  drawLighting(background);

  const foreground = new Container();
  foreground.zIndex = 900;
  drawForeground(foreground);
  app.stage.addChild(background, foreground);
}
