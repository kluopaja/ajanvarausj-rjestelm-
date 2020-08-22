//TODO functions to arrow functions
function make_day_editor_dom(time_grades, grade_descriptions, block_size,
                             member_id, poll_id, csrf_token) {
    let editor = new DayEditor(time_grades, grade_descriptions, block_size,
                               member_id, poll_id, csrf_token);
    return editor.dom;
}
function DayEditor(time_grades, grade_descriptions, block_size, member_id,
                  poll_id, csrf_token) {
    let self = this;
    this.handle_save = function() {
        let form = document.createElement('form');
        form.name = "form";
        form.action = '/new_time_preference';
        form.method = 'post';

        let data = document.createElement('input');
        data.name = 'data';
        data.value = JSON.stringify(self.new_grades);
        console.log(data.value);
        form.appendChild(data);

        let m_id = document.createElement('input')
        m_id.name = 'member_id';
        m_id.value = member_id;
        form.appendChild(m_id)

        
        let p_id = document.createElement('input');
        p_id.name = 'poll_id';
        console.log(poll_id)
        p_id.value = poll_id;
        form.appendChild(p_id)

        let csrf_t = document.createElement('input');
        csrf_t.name = 'csrf_token';
        csrf_t.value = csrf_token;
        form.appendChild(csrf_t)

        let submit = document.createElement('input');
        submit.type = 'submit';
        form.appendChild(submit);


        console.log(form.submit);
        //we need to attach the form somewhere to submit it 
        self.dom.appendChild(form);

        form.submit();
    }
    this.handle_reset = function() {
        let message = "Haluatko varmasti peruuttaa tallentamattomat muutokset?"
        if(window.confirm(message)) {
            self.init_new_grades();
            self.interface.reset();
            self.draw();
        }
    }
    this.handle_day_selection = function(e) {
        console.log('day selection change');
        console.log(self.time_grades);
        console.log('self ', self);
        let date = e.target.value;
        let date_idx = -1;
        for(let i = 0; i < self.time_grades.length; i++) {
            if(self.time_grades[i][0] == date) {
                date_idx = i
            }
        }
        if(date_idx >= 0) {
            self.selected_day = date_idx;
        }
        //reset the value after changing day selection
        //usually these are useless because similar effects should be
        //caused by the mouseout event
        self.interface.reset();
        self.draw();
    }
    this.handle_grade_selection = function(e) {
        console.log('grade_selection');
        self.selected_grade = parseInt(e.target.value);
        self.interface.reset();
        self.draw();
    }
    this.add_selection = function(start, end) {
        let grade = self.selected_grade;
        console.log('add selection ', start, end);
        self.new_grades[self.selected_day][1].push([start, end, grade]);
        self.draw();
    }
    this.draw = function() {
        let grades1 = self.time_grades[self.selected_day][1];
        let grades2 = self.new_grades[self.selected_day][1];
        self.interface.draw(grades1, grades2, self.selected_grade);
    }
    this.init_new_grades = function() {
        self.new_grades = [];
        for(let i = 0; i < self.time_grades.length; i++) {
            self.new_grades.push([self.time_grades[i][0], []]);
        }

    }
    self.time_grades = time_grades;
    self.new_grades = []
    this.init_new_grades();

    self.grade_descriptions = grade_descriptions;

    //resolution in minutes
    self.block_size = block_size;


    self.selected_day = 0;
    self.selected_grade = grade_descriptions.length-1;

    //initialize radio buttons 
    let day_selection = make_day_selection_dom(self.time_grades,
                                               self.handle_day_selection);
    let grade_selection = make_grade_selection_dom(self.grade_descriptions,
                                                   self.handle_grade_selection); 

    let save_reset = make_save_reset(self.handle_save, self.handle_reset);

    self.interface = new Interface(400, 1200, self.block_size,
                                   self.add_selection, self.draw);

    //create a parent dom and add the children
    self.dom = document.createElement('div');
    self.dom.appendChild(day_selection);
    self.dom.appendChild(document.createElement('br'));
    self.dom.appendChild(grade_selection);
    self.dom.appendChild(self.interface.canvas);
    self.dom.appendChild(save_reset);

    self.draw();
}
function make_day_selection_dom(time_grades, change) {
    let day_radios = document.createElement('div');
    day_radios.id = 'day_radios';
    for (let i = 0; i < time_grades.length; i++) {
        let label = document.createElement('label');
        label.htmlFor = time_grades[i][0];
        label.innerHTML = time_grades[i][0];
        day_radios.appendChild(label);

        let radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'day';
        radio.id = time_grades[i][0];
        radio.value = time_grades[i][0];
        if (i == 0) {
            radio.checked = true;
        }
        radio.addEventListener('change', change);
        day_radios.appendChild(radio);
        day_radios.appendChild(document.createElement('br'))
    }
    return day_radios;
}
function make_grade_selection_dom(grade_descriptions, change) {
    let grade_radios = document.createElement('div')
    grade_radios.id = 'grade_radios'
    for(let i = 0; i < grade_descriptions.length; i++) {
        let label = document.createElement('label');
        label.htmlFor = i.toString();
        label.innerHTML = grade_descriptions[i];
        grade_radios.appendChild(label);

        let radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'grade';
        radio.id = i.toString();
        radio.value = i;
        if(i+1 == grade_descriptions.length) {
            radio.checked = true;
        }
        radio.addEventListener('change', change);
        grade_radios.appendChild(radio)
    }
    return grade_radios;
}
function make_save_reset(save, reset) {
    let div = document.createElement('div');
    div.id = 'save_reset';
    let button = document.createElement('input');
    button.type = 'button';
    button.value = 'save';
    button.name = 'save';
    button.addEventListener('click', save);
    div.appendChild(button);
    button = document.createElement('input');
    button.type = 'button';
    button.value = 'reset';
    button.name = 'reset';
    button.addEventListener('click', reset);
    div.appendChild(button);
    return div;
}
//this is a bit useless class right now. Should this have info about the
//canvas width etc so it could return something like 'mouse_y_mins' etc?
function Mouse() {
    let self = this;
    self.x = 0;
    self.y = 0;
    self.is_active = false;
    this.update_pos = function(e) {
        self.is_active = true;
        self.x = e.offsetX;
        self.y = e.offsetY;
    }
    this.mouseout = function() {
        self.reset();
    }
    this.reset = function() {
        self.is_active = false;
    }
}
//stores all y values as minutes
function Selection() {
    let self = this;
    self.start_y = 0;
    self.y = 0;
    self.is_active = false;
    self.is_done = false;
    this.selectiondown = function() {
        if(self.is_active) {
            self.is_done = true;
            self.is_active = false;
        }
        else {
            self.is_active = true;
            self.start_y = self.y;
        }
    }
    this.selectionup = function() {
        if(self.is_active) {

            //TODO add some check that mouse has actually moved more than
            //some small amount
            //now might not behave well!
            if(self.y != self.start_y) {

                self.is_done = true;
                self.is_active = false;
            }
        }
    }
    this.selectionout = function() {
        self.reset();
    }
    this.reset = function() {
        self.is_active = false;
    }
    this.min_y = function() {
        return Math.min(self.start_y, self.y);
    }
    this.max_y = function() {
        return Math.max(self.start_y, self.y);
    }

}
function Time24(hour, min) {
    self = this;
    self.hour = hour;
    self.min = min;
}
//So this should handle all drawing things
//Also read mouse events
//also convert mouse x,y to minutes etc
//    This has to be done here because canvas is here
//also block size here but also elsewhere


//takes in data to draw
//maintains selections
//and then the selectiosn can be processed in DayEditor
function Interface(width, height, block_size, add_selection, draw_editor) {
    let self = this;

    this.handle_mousemove = function(e) {
        console.log('mousemove');
        self.mouse.update_pos(e);
        self.selection.y = self.y_to_min(self.mouse.y);
        self.update();
    }
    
    this.handle_mousedown = function(e) {
        console.log('mousedown');
        self.mouse.update_pos(e);
        self.selection.y = self.y_to_min(self.mouse.y);
        self.selection.selectiondown();
        self.update();
    }
    this.handle_mouseup = function(e) {
        console.log('mouseup');
        self.mouse.update_pos(e);
        self.selection.y = self.y_to_min(self.mouse.y);
        self.selection.selectionup();
        self.update();
    }
    this.handle_mouseout = function(e) {
        console.log('mouseout');
        self.mouse.mouseout();
        self.selection.selectionout();
        self.update();
    }

    //draws and also updates the childs if the state of interface changes
    //(i.e. width, height, block_size)
    this.update = function() {
        if(self.selection.is_done) {
            //callback
            add_selection(self.selection.min_y(), self.selection.max_y());
            self.selection.is_done = false;
        }
        draw_editor();
    }

    this.hour_to_y = function(h) {
        return Math.floor(h/24*self.canvas.height);
    }
    this.min_to_y = function(m) {
        return Math.floor(m/60/24*self.canvas.height);
    }
    //rounds everything to closest block
    this.y_to_min = function(y) {
        let mins = y*24*60/this.canvas.height;
        return Math.round(mins/self.block_size)*self.block_size
    }
    //rounds everything to closest block
    this.y_to_time = function(y) {
        let round_mins = self.y_to_min(y);
        let hours = Math.floor(round_mins/60)
        let result = new Time24(hours, round_mins%60);
        console.log('round_mins', round_mins);
        return result;
    }
    this.snap_to_blocks = function(y) {
        let time = self.y_to_time(y);
        return self.hour_to_y(time.hour) + self.min_to_y(time.min);
    }
    this.draw_intervals = function(intervals, colors) {
        for(let i = 0; i < intervals.length; i++) {
            let grade = parseInt(intervals[i][2]);
            self.ctx.fillStyle = colors.get(grade);
            let y_begin = self.min_to_y(intervals[i][0]);
            let y_end = self.min_to_y(intervals[i][1]);
            self.ctx.fillRect(0, y_begin, self.canvas.width, y_end-y_begin);
        }
    }
    //start and end are minutes!
    this.draw_active_selection = function(start, end, grade, colors) {
        start_y = self.min_to_y(start);
        end_y = self.min_to_y(end);
        
        start_y = self.snap_to_blocks(start_y);
        end_y = self.snap_to_blocks(end_y);
        color = colors.get(grade);
        console.log('selected grade', grade);
        self.ctx.save();
        self.ctx.fillStyle = color;
        self.ctx.globalAlpha = 0.9;
        self.ctx.fillRect(0, start_y, this.canvas.width, end_y-start_y);
        self.ctx.restore();
    }
    this.draw_mouse = function() {
        if(!self.mouse.is_active) {
            return;
        }
        let x = self.mouse.x;
        let y = self.mouse.y;
        //draw snap time line as bold
        self.ctx.beginPath();
        self.ctx.strokeStyle = 'black';
        self.ctx.lineWidth=4;
        self.ctx.moveTo(0, self.snap_to_blocks(y));
        self.ctx.lineTo(self.canvas.width, self.snap_to_blocks(y));
        self.ctx.stroke();

        //draw background box for the time
        self.ctx.fillStyle = 'rgb(245, 245, 245, 0.8)';
        self.ctx.fillRect(x, y-30, 90, 35)
        //draw current time
        let time = self.y_to_time(y);
        console.log('time', time);
        let hour_str = ('0' + time.hour).slice(-2);
        let min_str = ('0' + time.min).slice(-2);
        let time_str = hour_str + ':' + min_str;

        self.ctx.textBaseline = 'alphabetic';
        self.ctx.font = '30px Courier New';
        self.ctx.fillStyle = 'rgb(0, 0, 0)';
        self.ctx.fillText(time_str, x, y);
    }
    this.draw_time_grid = function() {
        //minor grid
        for(let i = 0; i < 24; i++) {
            self.ctx.beginPath();
            self.ctx.strokeStyle = 'rgb(0, 0, 0, 0.5)';
            self.ctx.lineWidth = 1;
            for(let j = 1; j < 4; j++) {
                //+0.5 is to make the anti-aliasing look better
                let y = self.hour_to_y(i) + self.min_to_y(j*15)+0.5
                self.ctx.moveTo(0, y);
                self.ctx.lineTo(self.canvas.width, y)
            }
            self.ctx.stroke()
        }

        //clear left side of the canvas for the labels
        self.ctx.fillStyle = 'whitesmoke';
        self.ctx.fillRect(0, 0, 40, self.canvas.height);
        //major grid
        for(let i = 0; i < 24; i++) {
            self.ctx.beginPath();
            self.ctx.strokeStyle = 'black';
            self.ctx.lineWidth = 2;
            self.ctx.moveTo(0, self.hour_to_y(i));
            self.ctx.lineTo(self.canvas.width, self.hour_to_y(i));
            self.ctx.stroke()
        }
        //major grid labels
        for(let i = 0; i < 24; i++) {
            self.ctx.fillStyle = 'black';
            self.ctx.textBaseline = 'top';
            self.ctx.font = '30px Courier New';
            hour_str = ('0' + i.toString()).slice(-2);
            self.ctx.fillText(hour_str, 0, self.hour_to_y(i))
        }
    }
    this.draw = function(old_grades, new_grades, selected_grade) {
        self.draw_time_grid();
        console.log('draw ', new_grades);
        self.draw_intervals(old_grades, self.grade_colors);

        self.draw_intervals(new_grades, self.grade_colors);

        if(self.selection.is_active) {
            self.draw_active_selection(self.selection.min_y(),
                                                self.selection.max_y(),
                                                selected_grade,
                                                self.active_colors);
        }
        self.draw_time_grid();
        self.draw_mouse();
    }
    this.reset = function() {
        self.mouse.reset();
        self.selection.reset();
    }

    //TODO just arrays
    self.grade_colors = new Map();
    self.grade_colors.set(2, 'rgb(60, 60, 60');
    self.grade_colors.set(1, 'silver');
    self.grade_colors.set(0, 'whitesmoke');
    self.active_colors = new Map();
    self.active_colors.set(2, 'rgb(60, 60, 60)');
    self.active_colors.set(1, 'silver');
    self.active_colors.set(0, 'whitesmoke');


    self.canvas = document.createElement('canvas');
    self.ctx = self.canvas.getContext('2d');
    self.canvas.width = width;
    self.canvas.height = height;

    self.selection = new Selection();
    self.mouse = new Mouse();

    self.canvas.addEventListener('mousemove', self.handle_mousemove);
    self.canvas.addEventListener('mousedown', self.handle_mousedown);
    self.canvas.addEventListener('mouseup', self.handle_mouseup);
    self.canvas.addEventListener('mouseout', self.handle_mouseout);

    self.block_size = block_size;
}

