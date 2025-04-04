/**
 * Chimera Animation Script
 * 
 * A particle-based animation that creates a flowing, multi-headed 
 * hydra effect inspired by the mythological Chimera.
 */

// Constants for animation
const HYDRA_HEADS = [
    { x: 0.2, y: 0.2, phase: 0, amplitude: 100, speed: 0.5, color: "#00FF41" },
    { x: 0.8, y: 0.2, phase: 0.7, amplitude: 120, speed: 0.6, color: "#00FFAA" },
    { x: 0.5, y: 0.3, phase: 1.4, amplitude: 150, speed: 0.4, color: "#00FF41" },
    { x: 0.3, y: 0.7, phase: 2.1, amplitude: 130, speed: 0.7, color: "#00FFAA" },
    { x: 0.7, y: 0.7, phase: 2.8, amplitude: 110, speed: 0.5, color: "#00FF41" },
    { x: 0.1, y: 0.5, phase: 3.5, amplitude: 140, speed: 0.6, color: "#00FFAA" },
    { x: 0.9, y: 0.5, phase: 4.2, amplitude: 160, speed: 0.4, color: "#00FF41" },
    { x: 0.5, y: 0.8, phase: 4.9, amplitude: 130, speed: 0.7, color: "#00FFAA" },
];

// Color scheme
const COLORS = {
    background: "#050A14",
    backgroundLight: "#0A1A2A",
    primary: "#00FF41",
    secondary: "#00FFAA",
    accent: "#00B140",
    text: "#E0E0E0",
    stars: "#FFFFFF"
};

class ChimeraAnimation {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.time = 0;
        this.mousePosition = { x: 0, y: 0 };
        this.isTouching = false;
        this.animationFrameId = null;
        this.flowParticles = [];
        this.starParticles = [];
        
        // Initialize hydra heads based on canvas size
        this.updateCanvasSize();
        
        // Bind methods
        this.animate = this.animate.bind(this);
        this.handleResize = this.handleResize.bind(this);
        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.handleTouchMove = this.handleTouchMove.bind(this);
        this.handleTouchStart = this.handleTouchStart.bind(this);
        this.handleTouchEnd = this.handleTouchEnd.bind(this);
        
        // Add event listeners
        window.addEventListener('resize', this.handleResize);
        this.canvas.addEventListener('mousemove', this.handleMouseMove);
        this.canvas.addEventListener('touchmove', this.handleTouchMove, { passive: false });
        this.canvas.addEventListener('touchstart', this.handleTouchStart);
        this.canvas.addEventListener('touchend', this.handleTouchEnd);
    }
    
    start() {
        this.createStars();
        this.createFlowParticles();
        this.animate();
    }
    
    stop() {
        window.removeEventListener('resize', this.handleResize);
        this.canvas.removeEventListener('mousemove', this.handleMouseMove);
        this.canvas.removeEventListener('touchmove', this.handleTouchMove);
        this.canvas.removeEventListener('touchstart', this.handleTouchStart);
        this.canvas.removeEventListener('touchend', this.handleTouchEnd);
        cancelAnimationFrame(this.animationFrameId);
    }
    
    updateCanvasSize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // Update hydra head positions for new canvas size
        this.hydraHeads = HYDRA_HEADS.map(head => ({
            ...head,
            x: head.x * this.canvas.width,
            y: head.y * this.canvas.height,
            amplitude: head.amplitude * (this.canvas.width / 1920)
        }));
    }
    
    createStars() {
        const starCount = Math.floor((this.canvas.width * this.canvas.height) / 5000);
        this.starParticles = [];
        
        for (let i = 0; i < starCount; i++) {
            this.starParticles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                size: Math.random() * 1.5 + 0.5,
                opacity: Math.random() * 0.7 + 0.3,
                pulse: Math.random() * 2,
            });
        }
    }
    
    createFlowParticles() {
        const particleCount = Math.floor((this.canvas.width * this.canvas.height) / 10000);
        this.flowParticles = [];
        
        for (let i = 0; i < particleCount; i++) {
            const headIndex = Math.floor(Math.random() * this.hydraHeads.length);
            const head = this.hydraHeads[headIndex];
            const angle = Math.random() * Math.PI * 2;
            const distance = Math.random() * 200;
            
            this.flowParticles.push({
                x: head.x + Math.cos(angle) * distance,
                y: head.y + Math.sin(angle) * distance,
                size: Math.random() * 3 + 1,
                color: head.color,
                speed: Math.random() * 2 + 1,
                angle,
                headIndex,
                life: Math.random() * 100 + 50,
                alpha: Math.random() * 0.5 + 0.3
            });
        }
    }
    
    getFlowVector(x, y, time) {
        let vx = 0;
        let vy = 0;
        
        // Combine influence from all hydra heads
        for (const head of this.hydraHeads) {
            const dx = x - head.x;
            const dy = y - head.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < head.amplitude * 3) {
                // Create a swirling effect around each head
                const angle = Math.atan2(dy, dx) + time * head.speed + head.phase;
                const force = Math.max(0, 1 - distance / (head.amplitude * 3));
                
                // Serpentine movement
                const swirl = Math.sin(angle * 2 + time * 0.5) * 0.5;
                
                vx += Math.cos(angle + swirl) * force * head.speed;
                vy += Math.sin(angle + swirl) * force * head.speed;
            }
        }
        
        return { vx, vy };
    }
    
    animate() {
        this.time += 0.01;
        
        // Clear and draw space background
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Create gradient background for space effect
        const gradient = this.ctx.createRadialGradient(
            this.canvas.width / 2, this.canvas.height / 2, 0,
            this.canvas.width / 2, this.canvas.height / 2, this.canvas.width * 0.7
        );
        gradient.addColorStop(0, COLORS.backgroundLight);
        gradient.addColorStop(1, COLORS.background);
        
        this.ctx.fillStyle = gradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw stars
        for (const star of this.starParticles) {
            const flickerAmount = Math.sin(this.time * 1.5 + star.pulse) * 0.2 + 0.8;
            this.ctx.globalAlpha = star.opacity * flickerAmount;
            this.ctx.fillStyle = COLORS.stars;
            this.ctx.beginPath();
            this.ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
            this.ctx.fill();
        }
        this.ctx.globalAlpha = 1;
        
        // Update hydra head positions with sinusoidal movement
        for (let i = 0; i < this.hydraHeads.length; i++) {
            const head = this.hydraHeads[i];
            // Create serpentine movement for each head
            head.x += Math.sin(this.time * head.speed + head.phase) * 2;
            head.y += Math.cos(this.time * head.speed * 0.7 + head.phase) * 1.5;
            
            // Keep heads within bounds
            head.x = Math.max(head.amplitude * 0.2, Math.min(this.canvas.width - head.amplitude * 0.2, head.x));
            head.y = Math.max(head.amplitude * 0.2, Math.min(this.canvas.height - head.amplitude * 0.2, head.y));
        }
        
        // Draw flow particles (hydra effect)
        for (let i = 0; i < this.flowParticles.length; i++) {
            const p = this.flowParticles[i];
            const head = this.hydraHeads[p.headIndex];
            
            // Update position based on flow field
            const angle = Math.atan2(p.y - head.y, p.x - head.x) + Math.sin(this.time * head.speed + p.headIndex) * 2;
            
            p.x += Math.cos(angle) * p.speed;
            p.y += Math.sin(angle) * p.speed;
            
            // Draw particle with glow effect
            this.ctx.globalAlpha = p.alpha * (p.life / 100);
            this.ctx.shadowBlur = 15;
            this.ctx.shadowColor = p.color;
            this.ctx.fillStyle = p.color;
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Reset shadow and alpha
            this.ctx.shadowBlur = 0;
            this.ctx.globalAlpha = 1;
            
            // Update life and regenerate if needed
            p.life--;
            if (p.life <= 0 || p.x < 0 || p.x > this.canvas.width || p.y < 0 || p.y > this.canvas.height) {
                // Reset particle to a new head
                const headIndex = Math.floor(Math.random() * this.hydraHeads.length);
                const newHead = this.hydraHeads[headIndex];
                const angle = Math.random() * Math.PI * 2;
                const distance = Math.random() * 100;
                
                p.x = newHead.x + Math.cos(angle) * distance;
                p.y = newHead.y + Math.sin(angle) * distance;
                p.headIndex = headIndex;
                p.life = Math.random() * 100 + 50;
                p.alpha = Math.random() * 0.5 + 0.3;
            }
        }
        
        // Draw hydra head connections (tentacles)
        this.ctx.lineWidth = 1.5;
        this.ctx.lineCap = "round";
        
        for (let i = 0; i < this.hydraHeads.length; i++) {
            const head1 = this.hydraHeads[i];
            const head2 = this.hydraHeads[(i + 1) % this.hydraHeads.length];
            
            // Create gradient for tentacle
            const gradient = this.ctx.createLinearGradient(head1.x, head1.y, head2.x, head2.y);
            gradient.addColorStop(0, head1.color + "40"); // Semi-transparent
            gradient.addColorStop(1, head2.color + "40"); // Semi-transparent
            
            this.ctx.strokeStyle = gradient;
            this.ctx.beginPath();
            
            // Draw curved path between heads
            this.ctx.moveTo(head1.x, head1.y);
            
            // Control points for curve
            const cpX1 = head1.x + (head2.x - head1.x) * 0.3 + Math.sin(this.time * 2 + i) * 50;
            const cpY1 = head1.y + (head2.y - head1.y) * 0.3 + Math.cos(this.time * 2 + i) * 50;
            const cpX2 = head1.x + (head2.x - head1.x) * 0.7 + Math.sin(this.time * 2 + i + 2) * 50;
            const cpY2 = head1.y + (head2.y - head1.y) * 0.7 + Math.cos(this.time * 2 + i + 2) * 50;
            
            this.ctx.bezierCurveTo(cpX1, cpY1, cpX2, cpY2, head2.x, head2.y);
            this.ctx.stroke();
        }
        
        // Draw hydra heads as glowing circles
        for (let i = 0; i < this.hydraHeads.length; i++) {
            const head = this.hydraHeads[i];
            
            // Outer glow
            const glowRadius = 20 + Math.sin(this.time * 2 + i) * 5;
            const gradient = this.ctx.createRadialGradient(
                head.x, head.y, 0,
                head.x, head.y, glowRadius
            );
            gradient.addColorStop(0, head.color + "80"); // Semi-transparent
            gradient.addColorStop(1, head.color + "00"); // Transparent
            
            this.ctx.fillStyle = gradient;
            this.ctx.beginPath();
            this.ctx.arc(head.x, head.y, glowRadius, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Core
            this.ctx.fillStyle = head.color;
            this.ctx.beginPath();
            this.ctx.arc(head.x, head.y, 5, 0, Math.PI * 2);
            this.ctx.fill();
        }
        
        this.animationFrameId = requestAnimationFrame(this.animate);
    }
    
    // Event handlers
    handleMove(x, y) {
        this.mousePosition.x = x;
        this.mousePosition.y = y;
    }
    
    handleMouseMove(e) {
        this.handleMove(e.clientX, e.clientY);
    }
    
    handleTouchMove(e) {
        if (e.touches.length > 0) {
            e.preventDefault();
            this.handleMove(e.touches[0].clientX, e.touches[0].clientY);
        }
    }
    
    handleTouchStart() {
        this.isTouching = true;
    }
    
    handleTouchEnd() {
        this.isTouching = false;
        this.mousePosition.x = 0;
        this.mousePosition.y = 0;
    }
    
    handleResize() {
        this.updateCanvasSize();
        this.createStars();
        this.createFlowParticles();
    }
}

// Initialize animation when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const animation = new ChimeraAnimation('chimera-canvas');
    animation.start();
    
    // Store animation instance on window for debugging
    window.chimeraAnimation = animation;
}); 