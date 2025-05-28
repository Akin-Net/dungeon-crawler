// frontend/src/components/sprites/GoblinSprite.jsx
import React from 'react';

// This component only renders the *internal parts* of the goblin.
// The outer .game-sprite div (for positioning on the grid) will be handled by DungeonCanvas.
const GoblinSprite = () => {
  return (
    <>
      <span className="goblin-component goblin-ear left"></span>
      <span className="goblin-component goblin-ear right"></span>
      <span className="goblin-component goblin-body"></span>
      <span className="goblin-component goblin-head">
        {/* Eyes are now separate spans, head pseudos are for nose/mouth */}
        <span className="goblin-component goblin-eye left-eye"></span>
        <span className="goblin-component goblin-eye right-eye"></span>
      </span>
    </>
  );
};

export default GoblinSprite;