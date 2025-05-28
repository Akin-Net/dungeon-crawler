import React from "react";

// This component only renders the *internal parts* of the player.
// The outer .game-sprite div (for positioning on the grid) will be handled by DungeonCanvas.
const PlayerSprite = () => {
  return (
    <div
          className={`game-sprite sprite-player`} 
          aria-label="Player"
          role="img"
        >
          <span className="knight-component knight-helmet"></span>
          <span className="knight-component knight-torso"></span>
          <span className="knight-component knight-shield"></span>
          <span className="knight-component knight-sword"></span>
        </div>
  );
};

export default PlayerSprite;