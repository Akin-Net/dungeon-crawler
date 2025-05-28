// frontend/src/__tests__/DungeonCanvas.test.jsx
import React from 'react';
import { render, screen, cleanup } from '@testing-library/react';
import DungeonCanvas from '../DungeonCanvas'; // Adjust path if necessary
import { LOCAL_TILE_TYPES as TILE_DEFS } from '../game_logic/initialState'; // Using an alias

// Keep track of the original getContext
const originalGetContext = HTMLCanvasElement.prototype.getContext;

describe('DungeonCanvas Component', () => {
  let mockCtx; // Declare here, define in beforeEach

  beforeEach(() => {
    // Define a fresh mock context for each test
    mockCtx = {
      fillRect: vi.fn(),
      clearRect: vi.fn(),
      beginPath: vi.fn(),
      arc: vi.fn(),
      fill: vi.fn(),
      fillText: vi.fn(),
      closePath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      font: '',
      textAlign: '',
      textBaseline: '',
      fillStyle: '', // Initial value for each test
      strokeStyle: '',
      lineWidth: 1,
    };

    HTMLCanvasElement.prototype.getContext = vi.fn(() => mockCtx);
    vi.clearAllMocks(); // Clear call counts on the functions within mockCtx
  });

  afterEach(() => {
    HTMLCanvasElement.prototype.getContext = originalGetContext;
    cleanup();
  });

  const TILE_SIZE = 20;

  const defaultProps = {
    dungeonMap: [
      [TILE_DEFS.WALL, TILE_DEFS.WALL, TILE_DEFS.WALL],
      [TILE_DEFS.WALL, TILE_DEFS.FLOOR, TILE_DEFS.WALL],
      [TILE_DEFS.WALL, TILE_DEFS.WALL, TILE_DEFS.WALL],
    ],
    playerPos: { x: 1, y: 1 },
    monsters: [],
    tileDefinitions: TILE_DEFS,
  };

  test('renders canvas element', () => {
    const { container } = render(<DungeonCanvas {...defaultProps} />);
    const canvasElement = container.querySelector('canvas');
    expect(canvasElement).toBeInTheDocument();
    expect(canvasElement.tagName).toBe('CANVAS');
  });

  test('clears canvas and sets dimensions on render', () => {
    const map = [
      [TILE_DEFS.FLOOR, TILE_DEFS.FLOOR],
      [TILE_DEFS.FLOOR, TILE_DEFS.FLOOR],
    ];
    const { container } = render(<DungeonCanvas {...defaultProps} dungeonMap={map} />);
    const canvasElement = container.querySelector('canvas');
    
    expect(canvasElement.width).toBe(map[0].length * TILE_SIZE);
    expect(canvasElement.height).toBe(map.length * TILE_SIZE);
    expect(mockCtx.clearRect).toHaveBeenCalledWith(0, 0, map[0].length * TILE_SIZE, map.length * TILE_SIZE);
  });

  test('does not attempt to draw if dungeonMap is null or empty', () => {
    render(<DungeonCanvas {...defaultProps} dungeonMap={null} />);
    expect(mockCtx.clearRect).not.toHaveBeenCalled();

    cleanup(); 
    vi.clearAllMocks();
    HTMLCanvasElement.prototype.getContext = vi.fn(() => mockCtx);


    render(<DungeonCanvas {...defaultProps} dungeonMap={[]} />);
    expect(mockCtx.clearRect).not.toHaveBeenCalled();
  });


  describe('Tile Rendering', () => {
    test('renders FLOOR tiles correctly', () => {
      const map = [[TILE_DEFS.FLOOR]];
      render(
        <DungeonCanvas 
          dungeonMap={map} 
          playerPos={{ x: 99, y: 99 }} 
          monsters={[]} 
          tileDefinitions={TILE_DEFS} 
        />
      );
      
      expect(mockCtx.fillRect).toHaveBeenCalledWith(0, 0, TILE_SIZE, TILE_SIZE);
      expect(mockCtx.fillStyle.toLowerCase()).toBe('#888'); 
    });

    test('renders WALL tiles correctly', () => {
      const map = [[TILE_DEFS.WALL]];
      render(<DungeonCanvas {...defaultProps} dungeonMap={map} playerPos={{x:99, y:99}} monsters={[]}/>); 
      expect(mockCtx.fillRect).toHaveBeenCalledWith(0, 0, TILE_SIZE, TILE_SIZE);
      expect(mockCtx.fillStyle.toLowerCase()).toBe('#333'); 
    });
    
    test('renders FOG tiles correctly', () => {
      const map = [[TILE_DEFS.FOG]];
      render(<DungeonCanvas {...defaultProps} dungeonMap={map} playerPos={{x:99, y:99}} monsters={[]}/>);
      expect(mockCtx.fillRect).toHaveBeenCalledWith(0, 0, TILE_SIZE, TILE_SIZE);
      expect(mockCtx.fillStyle.toLowerCase()).toBe('#1a1a1a'); 
    });

    test('renders DOOR_CLOSED tiles with detail', () => {
      const map = [[TILE_DEFS.DOOR_CLOSED]];
      render(<DungeonCanvas {...defaultProps} dungeonMap={map} playerPos={{x:99, y:99}} monsters={[]}/>);
      
      const fillRectCalls = mockCtx.fillRect.mock.calls;
      expect(fillRectCalls).toEqual(
        expect.arrayContaining([
          [0, 0, TILE_SIZE, TILE_SIZE], 
          [ 
            0 * TILE_SIZE + TILE_SIZE * 0.7, 
            0 * TILE_SIZE + TILE_SIZE * 0.4, 
            TILE_SIZE * 0.15, 
            TILE_SIZE * 0.2
          ]
        ])
      );
    });
    
    test('renders DOOR_OPEN tiles with detail', () => {
      const map = [[TILE_DEFS.DOOR_OPEN]];
      render(<DungeonCanvas {...defaultProps} dungeonMap={map} playerPos={{x:99, y:99}} monsters={[]}/>);
      
      const fillRectCalls = mockCtx.fillRect.mock.calls;
      expect(fillRectCalls.length).toBeGreaterThanOrEqual(2); 
      expect(fillRectCalls).toEqual(
        expect.arrayContaining([
            [0 * TILE_SIZE, 0 * TILE_SIZE, TILE_SIZE, TILE_SIZE], 
        ])
      );
    });

    test('renders STAIRS_DOWN tiles with detail', () => {
        const map = [[TILE_DEFS.STAIRS_DOWN]];
        render(<DungeonCanvas {...defaultProps} dungeonMap={map} playerPos={{x:99, y:99}} monsters={[]}/>);
        
        expect(mockCtx.fillRect.mock.calls.length).toBeGreaterThanOrEqual(1 + 4); 
        expect(mockCtx.beginPath).toHaveBeenCalledTimes(1); 
        expect(mockCtx.moveTo).toHaveBeenCalled();
        expect(mockCtx.lineTo).toHaveBeenCalledTimes(2);
        expect(mockCtx.closePath).toHaveBeenCalledTimes(1);
        expect(mockCtx.fill).toHaveBeenCalledTimes(1); 
      });

    test('renders ITEM_POTION tiles with "P" character', () => {
      const map = [[TILE_DEFS.ITEM_POTION]];
      render(<DungeonCanvas {...defaultProps} dungeonMap={map} playerPos={{x:99, y:99}} monsters={[]}/>);
      expect(mockCtx.fillRect).toHaveBeenCalledWith(0, 0, TILE_SIZE, TILE_SIZE);
      expect(mockCtx.fillText).toHaveBeenCalledWith('P', TILE_SIZE / 2, TILE_SIZE / 2 + 1);
    });
    
    test('renders ITEM_SCROLL_TELEPORT tiles with "S" character', () => {
      const map = [[TILE_DEFS.ITEM_SCROLL_TELEPORT]];
      render(<DungeonCanvas {...defaultProps} dungeonMap={map} playerPos={{x:99, y:99}} monsters={[]}/>);
      expect(mockCtx.fillRect).toHaveBeenCalledWith(0, 0, TILE_SIZE, TILE_SIZE);
      expect(mockCtx.fillText).toHaveBeenCalledWith('S', TILE_SIZE / 2, TILE_SIZE / 2 + 1);
    });
  });

  describe('Player Rendering', () => {
    test('renders player at correct position if not in FOG', () => {
      const playerPos = { x: 1, y: 1 };
      const map = [
        [TILE_DEFS.FLOOR, TILE_DEFS.FLOOR, TILE_DEFS.FLOOR],
        [TILE_DEFS.FLOOR, TILE_DEFS.FLOOR, TILE_DEFS.FLOOR], 
        [TILE_DEFS.FLOOR, TILE_DEFS.FLOOR, TILE_DEFS.FLOOR],
      ];
      render(<DungeonCanvas {...defaultProps} playerPos={playerPos} dungeonMap={map} />);
      
      expect(mockCtx.beginPath).toHaveBeenCalled();
      expect(mockCtx.arc).toHaveBeenCalledWith(
        playerPos.x * TILE_SIZE + TILE_SIZE / 2,
        playerPos.y * TILE_SIZE + TILE_SIZE / 2,
        TILE_SIZE / 3, 0, 2 * Math.PI
      );
      expect(mockCtx.fill).toHaveBeenCalled(); 
      expect(mockCtx.fillText).toHaveBeenCalledWith('@', playerPos.x * TILE_SIZE + TILE_SIZE / 2, playerPos.y * TILE_SIZE + TILE_SIZE / 2 + 1);
    });

    test('does not render player if playerPos is on a FOG tile', () => {
      const playerPos = { x: 1, y: 1 };
      const map = [
        [TILE_DEFS.FOG, TILE_DEFS.FOG, TILE_DEFS.FOG],
        [TILE_DEFS.FOG, TILE_DEFS.FOG, TILE_DEFS.FOG], 
        [TILE_DEFS.FOG, TILE_DEFS.FOG, TILE_DEFS.FOG],
      ];
      render(<DungeonCanvas {...defaultProps} playerPos={playerPos} dungeonMap={map} />);
      
      const playerArcCall = mockCtx.arc.mock.calls.find(call => 
        call[0] === playerPos.x * TILE_SIZE + TILE_SIZE / 2 &&
        call[1] === playerPos.y * TILE_SIZE + TILE_SIZE / 2 &&
        call[2] === TILE_SIZE / 3 
      );
      const playerTextCall = mockCtx.fillText.mock.calls.find(call => call[0] === '@');
      
      expect(playerArcCall).toBeUndefined();
      expect(playerTextCall).toBeUndefined();
    });
  });

  describe('Monster Rendering', () => {
    const monster1 = { id: 'g1', type: 'goblin', x: 0, y: 0, tile_id: TILE_DEFS.MONSTER_GOBLIN };
    const monster2 = { id: 'o1', type: 'orc', x: 2, y: 2, tile_id: TILE_DEFS.MONSTER_ORC };
    const monsterInFog = { id: 's1', type: 'skeleton', x: 0, y: 2, tile_id: TILE_DEFS.MONSTER_SKELETON };

    test('renders visible monsters correctly (goblin and orc)', () => {
      const map = [
        [TILE_DEFS.FLOOR, TILE_DEFS.FLOOR, TILE_DEFS.FLOOR],
        [TILE_DEFS.FLOOR, TILE_DEFS.FLOOR, TILE_DEFS.FLOOR],
        [TILE_DEFS.FOG,   TILE_DEFS.FLOOR, TILE_DEFS.FLOOR], 
      ];
      render(<DungeonCanvas {...defaultProps} playerPos={{x:1,y:1}} dungeonMap={map} monsters={[monster1, monster2, monsterInFog]} />);

      expect(mockCtx.arc).toHaveBeenCalledWith(
        monster1.x * TILE_SIZE + TILE_SIZE / 2,
        monster1.y * TILE_SIZE + TILE_SIZE / 2,
        TILE_SIZE / 2.5, 0, 2 * Math.PI
      );
      expect(mockCtx.fillText).toHaveBeenCalledWith('g', monster1.x * TILE_SIZE + TILE_SIZE / 2, monster1.y * TILE_SIZE + TILE_SIZE / 2 + 1);

      expect(mockCtx.arc).toHaveBeenCalledWith(
        monster2.x * TILE_SIZE + TILE_SIZE / 2,
        monster2.y * TILE_SIZE + TILE_SIZE / 2,
        TILE_SIZE / 2.5, 0, 2 * Math.PI
      );
      expect(mockCtx.fillText).toHaveBeenCalledWith('O', monster2.x * TILE_SIZE + TILE_SIZE / 2, monster2.y * TILE_SIZE + TILE_SIZE / 2 + 1);
      
      const skeletonArcCall = mockCtx.arc.mock.calls.find(call =>
        call[0] === monsterInFog.x * TILE_SIZE + TILE_SIZE / 2 &&
        call[1] === monsterInFog.y * TILE_SIZE + TILE_SIZE / 2
      );
      const skeletonTextCall = mockCtx.fillText.mock.calls.find(call => call[0] === 'S'); 
      
      expect(skeletonArcCall).toBeUndefined();
      expect(skeletonTextCall).toBeUndefined();
    });

    test('does not render monsters if monsters prop is empty or null', () => {
      const map = [[TILE_DEFS.FLOOR]];
      const playerPosOnFloor = {x:0, y:0};

      render(<DungeonCanvas {...defaultProps} dungeonMap={map} playerPos={playerPosOnFloor} monsters={[]} />);
      const callsAfterPlayerOnly = {
        arc: mockCtx.arc.mock.calls.length,
        fillText: mockCtx.fillText.mock.calls.length
      };
      
      cleanup(); vi.clearAllMocks(); HTMLCanvasElement.prototype.getContext = vi.fn(() => mockCtx);

      render(<DungeonCanvas {...defaultProps} dungeonMap={map} playerPos={playerPosOnFloor} monsters={null} />);
      expect(mockCtx.arc.mock.calls.length).toBe(callsAfterPlayerOnly.arc);
      expect(mockCtx.fillText.mock.calls.length).toBe(callsAfterPlayerOnly.fillText);
    });
  });
});