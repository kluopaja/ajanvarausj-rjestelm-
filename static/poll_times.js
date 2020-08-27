//TODO functions to arrow functions
function makeDayEditorDom(timeGrades, gradeDescriptions, blockSize,
                             memberId, pollId, csrfToken) {
    let editor = new DayEditor(timeGrades, gradeDescriptions, blockSize,
                               memberId, pollId, csrfToken);
    return editor.dom;
}
function DayEditor(timeGrades, gradeDescriptions, blockSize, memberId,
                  pollId, csrfToken) {
    let self = this;
    this.handleSave = function() {
        let form = document.createElement('form');
        form.name = "form";
        form.action = '/new_time_preference';
        form.method = 'post';

        let data = document.createElement('input');
        data.name = 'data';
        data.value = JSON.stringify(self.newGrades);
        console.log(data.value);
        form.appendChild(data);

        let mId = document.createElement('input')
        mId.name = 'member_id';
        mId.value = memberId;
        form.appendChild(mId)


        let pId = document.createElement('input');
        pId.name = 'poll_id';
        console.log(pollId)
        pId.value = pollId;
        form.appendChild(pId)

        let csrfT = document.createElement('input');
        csrfT.name = 'csrf_token';
        csrfT.value = csrfToken;
        form.appendChild(csrfT)

        let submit = document.createElement('input');
        submit.type = 'submit';
        form.appendChild(submit);


        console.log(form.submit);
        //we need to attach the form somewhere to submit it
        self.dom.appendChild(form);

        form.submit();
    }
    this.handleReset = function() {
        let message = "Haluatko varmasti peruuttaa tallentamattomat muutokset?"
        if(window.confirm(message)) {
            self.initNewGrades();
            self.interface.reset();
            self.draw();
        }
    }
    this.handleDaySelection = function(e) {
        console.log('day selection change');
        console.log(self.timeGrades);
        console.log('self ', self);
        let date = e.target.value;
        let dateIdx = -1;
        for(let i = 0; i < self.timeGrades.length; i++) {
            if(self.timeGrades[i][0] == date) {
                dateIdx = i
            }
        }
        if(dateIdx >= 0) {
            self.selectedDay = dateIdx;
        }
        //reset the value after changing day selection
        //usually these are useless because similar effects should be
        //caused by the mouseout event
        self.interface.reset();
        self.draw();
    }
    this.handleGradeSelection = function(e) {
        console.log('grade_selection');
        self.selectedGrade = parseInt(e.target.value);
        self.interface.reset();
        self.draw();
    }
    this.addSelection = function(start, end) {
        let grade = self.selectedGrade;
        console.log('add selection ', start, end);
        self.newGrades[self.selectedDay][1].push([start, end, grade]);
        self.draw();
    }
    this.draw = function() {
        let grades1 = self.timeGrades[self.selectedDay][1];
        let grades2 = self.newGrades[self.selectedDay][1];
        self.interface.draw(grades1, grades2, self.selectedGrade);
    }
    this.initNewGrades = function() {
        self.newGrades = [];
        for(let i = 0; i < self.timeGrades.length; i++) {
            self.newGrades.push([self.timeGrades[i][0], []]);
        }

    }
    self.timeGrades = timeGrades;
    self.newGrades = []
    this.initNewGrades();

    self.gradeDescriptions = gradeDescriptions;

    //resolution in minutes
    self.blockSize = blockSize;


    self.selectedDay = 0;
    self.selectedGrade = gradeDescriptions.length-1;

    self.interface = new Interface(400, 1200, self.blockSize,
                                   self.addSelection, self.draw);
    //initialize radio buttons
    let daySelection = makeDaySelectionDom(self.timeGrades,
                                               self.handleDaySelection);
    let gradeSelection = makeGradeSelectionDom(self.gradeDescriptions,
                                                   self.interface.gradeColors,
                                                   self.handleGradeSelection);

    let saveReset = makeSaveReset(self.handleSave, self.handleReset);


    //create a parent dom and add the children
    self.dom = document.createElement('div');
    self.dom.appendChild(daySelection);
    self.dom.appendChild(document.createElement('br'));
    self.dom.appendChild(gradeSelection);
    self.dom.appendChild(saveReset);
    self.dom.appendChild(self.interface.canvas);

    self.draw();
}
function makeDaySelectionDom(timeGrades, change) {
    let dayRadios = document.createElement('div');
    dayRadios.id = 'day_radios';

    let header = document.createElement('h3');
    header.innerHTML = "Valitse muokattava päivä";
    dayRadios.appendChild(header)
    for (let i = 0; i < timeGrades.length; i++) {
        let label = document.createElement('label');
        label.htmlFor = timeGrades[i][0];
        label.innerHTML = timeGrades[i][0];
        dayRadios.appendChild(label);

        let radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'day';
        radio.id = timeGrades[i][0];
        radio.value = timeGrades[i][0];
        if (i == 0) {
            radio.checked = true;
        }
        radio.addEventListener('change', change);
        dayRadios.appendChild(radio);
        dayRadios.appendChild(document.createElement('br'))
    }
    return dayRadios;
}
function makeGradeSelectionDom(gradeDescriptions, gradeColors, change) {
    let gradeRadios = document.createElement('div')
    gradeRadios.id = 'grade_radios'
    let header = document.createElement('h3');
    header.innerHTML = "Valitse lisättävän toiveen tyyppi";
    gradeRadios.appendChild(header)
    for(let i = 0; i < gradeDescriptions.length; i++) {
        let label = document.createElement('label');
        label.htmlFor = i.toString();
        label.innerHTML = gradeDescriptions[i];

        gradeRadios.appendChild(label);
        let colorSpan = document.createElement('span');
        colorSpan.innerHTML = "";
        colorSpan.style.background = gradeColors.get(i);
        label.appendChild(colorSpan);


        let radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'grade';
        radio.id = i.toString();
        radio.value = i;
        if(i+1 == gradeDescriptions.length) {
            radio.checked = true;
        }
        radio.addEventListener('change', change);
        gradeRadios.appendChild(radio)
        gradeRadios.appendChild(document.createElement('br'));
    }
    return gradeRadios;
}
function makeSaveReset(save, reset) {
    let div = document.createElement('div');
    div.id = 'save_reset';
    let button = document.createElement('input');
    button.type = 'button';
    button.value = 'Tallenna muutokset';
    button.name = 'save';
    button.addEventListener('click', save);
    div.appendChild(button);
    button = document.createElement('input');
    button.type = 'button';
    button.value = 'Peruuta muutokset';
    button.name = 'reset';
    button.addEventListener('click', reset);
    div.appendChild(button);
    return div;
}
//this is a bit useless class right now. Should this have info about the
//canvas width etc so it could return something like 'mouseYMins' etc?
function Mouse() {
    let self = this;
    self.x = 0;
    self.y = 0;
    self.isActive = false;
    this.updatePos = function(e) {
        self.isActive = true;
        self.x = e.offsetX;
        self.y = e.offsetY;
    }
    this.mouseout = function() {
        self.reset();
    }
    this.reset = function() {
        self.isActive = false;
    }
}
//stores all y values as minutes
function Selection() {
    let self = this;
    self.startY = 0;
    self.y = 0;
    self.isActive = false;
    self.isDone = false;
    this.selectiondown = function() {
        if(self.isActive) {
            self.isDone = true;
            self.isActive = false;
        }
        else {
            self.isActive = true;
            self.startY = self.y;
        }
    }
    this.selectionup = function() {
        if(self.isActive) {

            //TODO add some check that mouse has actually moved more than
            //some small amount
            //now might not behave well!
            if(self.y != self.startY) {

                self.isDone = true;
                self.isActive = false;
            }
        }
    }
    this.selectionout = function() {
        self.reset();
    }
    this.reset = function() {
        self.isActive = false;
    }
    this.minY = function() {
        return Math.min(self.startY, self.y);
    }
    this.maxY = function() {
        return Math.max(self.startY, self.y);
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
function Interface(width, height, blockSize, addSelection, drawEditor) {
    let self = this;

    this.handleMousemove = function(e) {
        console.log('mousemove');
        self.mouse.updatePos(e);
        self.selection.y = self.yToMin(self.mouse.y);
        self.update();
    }

    this.handleMousedown = function(e) {
        console.log('mousedown');
        self.mouse.updatePos(e);
        self.selection.y = self.yToMin(self.mouse.y);
        self.selection.selectiondown();
        self.update();
    }
    this.handleMouseup = function(e) {
        console.log('mouseup');
        self.mouse.updatePos(e);
        self.selection.y = self.yToMin(self.mouse.y);
        self.selection.selectionup();
        self.update();
    }
    this.handleMouseout = function(e) {
        console.log('mouseout');
        self.mouse.mouseout();
        self.selection.selectionout();
        self.update();
    }

    //draws and also updates the childs if the state of interface changes
    //(i.e. width, height, blockSize)
    this.update = function() {
        if(self.selection.isDone) {
            //callback
            addSelection(self.selection.minY(), self.selection.maxY());
            self.selection.isDone = false;
        }
        drawEditor();
    }

    this.hourToY = function(h) {
        return Math.floor(h/24*self.canvas.height);
    }
    this.minToY = function(m) {
        return Math.floor(m/60/24*self.canvas.height);
    }
    //rounds everything to closest block
    this.yToMin = function(y) {
        let mins = y*24*60/this.canvas.height;
        return Math.round(mins/self.blockSize)*self.blockSize
    }
    //rounds everything to closest block
    this.yToTime = function(y) {
        let roundMins = self.yToMin(y);
        let hours = Math.floor(roundMins/60)
        let result = new Time24(hours, roundMins%60);
        console.log('round_mins', roundMins);
        return result;
    }
    this.snapToBlocks = function(y) {
        let time = self.yToTime(y);
        return self.hourToY(time.hour) + self.minToY(time.min);
    }
    this.drawIntervals = function(intervals, colors) {
        for(let i = 0; i < intervals.length; i++) {
            let grade = parseInt(intervals[i][2]);
            self.ctx.fillStyle = colors.get(grade);
            let yBegin = self.minToY(intervals[i][0]);
            let yEnd = self.minToY(intervals[i][1]);
            self.ctx.fillRect(0, yBegin, self.canvas.width, yEnd-yBegin);
        }
    }
    //start and end are minutes!
    this.drawActiveSelection = function(start, end, grade, colors) {
        startY = self.minToY(start);
        endY = self.minToY(end);

        startY = self.snapToBlocks(startY);
        endY = self.snapToBlocks(endY);
        color = colors.get(grade);
        console.log('selected grade', grade);
        self.ctx.save();
        self.ctx.fillStyle = color;
        self.ctx.globalAlpha = 0.9;
        self.ctx.fillRect(0, startY, this.canvas.width, endY-startY);
        self.ctx.restore();
    }
    this.drawMouse = function() {
        if(!self.mouse.isActive) {
            return;
        }
        let x = self.mouse.x;
        let y = self.mouse.y;
        //draw snap time line as bold
        self.ctx.beginPath();
        self.ctx.strokeStyle = 'black';
        self.ctx.lineWidth=4;
        self.ctx.moveTo(0, self.snapToBlocks(y));
        self.ctx.lineTo(self.canvas.width, self.snapToBlocks(y));
        self.ctx.stroke();

        //draw background box for the time
        self.ctx.fillStyle = 'rgb(245, 245, 245, 0.8)';
        self.ctx.fillRect(x, y-30, 90, 35)
        //draw current time
        let time = self.yToTime(y);
        console.log('time', time);
        let hourStr = ('0' + time.hour).slice(-2);
        let minStr = ('0' + time.min).slice(-2);
        let timeStr = hourStr + ':' + minStr;

        self.ctx.textBaseline = 'alphabetic';
        self.ctx.font = '30px Courier New';
        self.ctx.fillStyle = 'rgb(0, 0, 0)';
        self.ctx.fillText(timeStr, x, y);
    }
    this.drawTimeGrid = function() {
        //minor grid
        for(let i = 0; i < 24; i++) {
            self.ctx.beginPath();
            self.ctx.strokeStyle = 'rgb(0, 0, 0, 0.5)';
            self.ctx.lineWidth = 1;
            for(let j = 1; j < 4; j++) {
                //+0.5 is to make the anti-aliasing look better
                let y = self.hourToY(i) + self.minToY(j*15)+0.5
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
            self.ctx.moveTo(0, self.hourToY(i));
            self.ctx.lineTo(self.canvas.width, self.hourToY(i));
            self.ctx.stroke()
        }
        //major grid labels
        for(let i = 0; i < 24; i++) {
            self.ctx.fillStyle = 'black';
            self.ctx.textBaseline = 'top';
            self.ctx.font = '30px Courier New';
            hourStr = ('0' + i.toString()).slice(-2);
            self.ctx.fillText(hourStr, 0, self.hourToY(i))
        }
    }
    this.draw = function(oldGrades, newGrades, selectedGrade) {
        self.drawTimeGrid();
        console.log('draw ', newGrades);
        self.drawIntervals(oldGrades, self.gradeColors);

        self.drawIntervals(newGrades, self.gradeColors);

        if(self.selection.isActive) {
            self.drawActiveSelection(self.selection.minY(),
                                                self.selection.maxY(),
                                                selectedGrade,
                                                self.activeColors);
        }
        self.drawTimeGrid();
        self.drawMouse();
    }
    this.reset = function() {
        self.mouse.reset();
        self.selection.reset();
    }

    //TODO just arrays
    self.gradeColors = new Map();
    self.gradeColors.set(2, 'rgb(60, 60, 60');
    self.gradeColors.set(1, 'silver');
    self.gradeColors.set(0, 'whitesmoke');
    self.activeColors = new Map();
    self.activeColors.set(2, 'rgb(60, 60, 60)');
    self.activeColors.set(1, 'silver');
    self.activeColors.set(0, 'whitesmoke');


    self.canvas = document.createElement('canvas');
    self.ctx = self.canvas.getContext('2d');
    self.canvas.width = width;
    self.canvas.height = height;

    self.selection = new Selection();
    self.mouse = new Mouse();

    self.canvas.addEventListener('mousemove', self.handleMousemove);
    self.canvas.addEventListener('mousedown', self.handleMousedown);
    self.canvas.addEventListener('mouseup', self.handleMouseup);
    self.canvas.addEventListener('mouseout', self.handleMouseout);

    self.blockSize = blockSize;
}

