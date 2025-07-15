import { wpmChart, volumeChart, pitchChart } from './state.js';

// Retrieves and assigns the value of theme from the browsers localStorage (or defaults to 'light')
let currentTheme = localStorage.getItem('theme') || 'light';

 // Sets up the theme for the app when its loaded
 function initialiseTheme() {
    //'data-theme' is in the attribute in <html>
    //  - document.documentElement refers to the root <html> element of the page 
    //  - setAttribute is a built-in DOM API method available in JS
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeUI();

    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

function updateThemeUI() {
    // Light and Dark Mode  
    const themeIcon = document.getElementById('themeIcon');
    const themeText = document.getElementById('themeText');
    
    if (currentTheme === 'dark') {
        themeIcon.textContent = '☀️';
        themeText.textContent = 'Light Mode';
    } else {
        themeIcon.textContent = '🌙';
        themeText.textContent = 'Dark Mode';
    }
}

// Toggle theme function
function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('theme', currentTheme);
    
    updateThemeUI();
    updateChartColors();
}

// Update chart colors based on theme
function updateChartColors() {
    const isDark = currentTheme === 'dark';
    const textColor = isDark ? '#e0e0e0' : '#222';
    const gridColor = isDark ? '#444' : '#ddd';
    
    // Array of all chart objects (imported from state.js)
    [wpmChart, volumeChart, pitchChart].forEach(chart => {
        if (chart) {
            chart.options.color = textColor;
            chart.options.scales.x.grid.color = gridColor;
            chart.options.scales.x.ticks.color = textColor;
            chart.options.scales.y.grid.color = gridColor;
            chart.options.scales.y.ticks.color = textColor;
            chart.update('none'); // Apply the changes without animation 
        }
    });
}

export { initialiseTheme, updateChartColors, currentTheme };
