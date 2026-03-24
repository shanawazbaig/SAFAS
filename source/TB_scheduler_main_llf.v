//                ___   _   ___ _   ___
//               / __| /_\ | __/_\ / __|
//               \__ \/ _ \| _/ _ \\__ \
//               |___/_/ \_|_/_/ \_|___/
//
// Author:          LLF Hybrid Implementation
// Modified Date:   March 24, 2026
// Project Name:    SAFAS (Secure and Fast Hardware Scheduler)
// Target Device:   Virtex Family FPGA
// Tool versions:   Vivado 2018.2
//
// Licence:         These project have been published for academic use only under GPLv3 License.
//                  Copyright  2021-2026
//                  All Rights Reserved
//
// Description:     Testbench for LLF Hybrid Scheduler
//                  Verifies the LLF hybrid scheduling behavior with laxity threshold
// 010100101000000100011010000001010011

`timescale 1ns / 1ns
module TB_scheduler_main_llf();

parameter W = 42;
parameter R_Q = 64;
parameter CORE = 16;

reg clk, rst;
reg wr;
reg [W-2:0] task_in;

wire CTRL_RP;
wire CTRL_subtract;
wire CTRL_MQ_active;
wire v_exch;
wire [W-2:0] task_exch;

// Instantiate the LLF hybrid scheduler
Scheduler_main_llf #(.W(W), .R_Q(R_Q), .CORE(CORE)) UUT (
    .clk(clk),
    .rst(rst),
    .wr(wr),
    .task_in(task_in),
    .CTRL_RP(CTRL_RP),
    .CTRL_subtract(CTRL_subtract),
    .CTRL_MQ_active(CTRL_MQ_active),
    .v_exch(v_exch),
    .task_exch(task_exch)
);

// Clock generation
initial begin
    clk = 0;
    forever #5 clk = ~clk;
end

// Test stimulus
initial begin
    rst = 1;
    wr = 0;
    task_in = 0;

    #20 rst = 0;

    // Test Case 1: Task with high laxity (should use SRJF)
    // Task: ID=1, Deadline=100, Execution=20, Laxity=80 > 30 (1.5×20)
    #10;
    @(posedge clk);
    if(CTRL_MQ_active) begin
        wr = 1;
        task_in = {8'd1, 16'd100, 16'd20}; // ID=1, D=100, E=20
        @(posedge clk);
        wr = 0;
    end

    // Test Case 2: Task with low laxity (should switch to LLF)
    // Task: ID=2, Deadline=25, Execution=20, Laxity=5 < 30 (1.5×20)
    #100;
    @(posedge clk);
    if(CTRL_MQ_active) begin
        wr = 1;
        task_in = {8'd2, 16'd25, 16'd20}; // ID=2, D=25, E=20 - Low laxity!
        @(posedge clk);
        wr = 0;
    end

    // Test Case 3: Multiple tasks with different laxities
    #100;
    @(posedge clk);
    if(CTRL_MQ_active) begin
        // Task with moderate laxity
        wr = 1;
        task_in = {8'd3, 16'd50, 16'd15}; // ID=3, D=50, E=15, Laxity=35 > 22.5
        @(posedge clk);
        wr = 0;
        #10;

        // Task with very low laxity
        wr = 1;
        task_in = {8'd4, 16'd22, 16'd20}; // ID=4, D=22, E=20, Laxity=2 < 30
        @(posedge clk);
        wr = 0;
        #10;

        // Short task (SRJF should prioritize)
        wr = 1;
        task_in = {8'd5, 16'd60, 16'd5}; // ID=5, D=60, E=5, Laxity=55 > 7.5
        @(posedge clk);
        wr = 0;
    end

    // Test Case 4: Borderline laxity cases
    #200;
    @(posedge clk);
    if(CTRL_MQ_active) begin
        // Task at threshold: laxity = 1.5 × execution
        wr = 1;
        task_in = {8'd6, 16'd45, 16'd30}; // ID=6, D=45, E=30, Laxity=15 (threshold=45)
        @(posedge clk);
        wr = 0;
        #10;

        // Task just below threshold
        wr = 1;
        task_in = {8'd7, 16'd44, 16'd30}; // ID=7, D=44, E=30, Laxity=14 < 45
        @(posedge clk);
        wr = 0;
        #10;

        // Task just above threshold
        wr = 1;
        task_in = {8'd8, 16'd46, 16'd30}; // ID=8, D=46, E=30, Laxity=16 > 45
        @(posedge clk);
        wr = 0;
    end

    // Run simulation
    #5000;

    // Display statistics
    $display("========================================");
    $display("LLF Hybrid Scheduler Statistics");
    $display("========================================");
    $display("Total tasks received: %d", UUT.Scheduler.RP_RECEIVED);
    $display("Tasks scheduled via SRJF: %d", UUT.Scheduler.RP_SRJF_scheduled);
    $display("Tasks scheduled via LLF: %d", UUT.Scheduler.RP_LLF_scheduled);
    $display("Tasks preempted: %d", UUT.Scheduler.RP_preempted);
    $display("Tasks exchanged (overflow): %d", UUT.Scheduler.RP_Exchanged);
    $display("========================================");
    $display("Algorithm: LLF Hybrid");
    $display("Threshold: 1.5× execution time");
    $display("Low laxity uses LLF queue");
    $display("High laxity uses SRJF queue");
    $display("========================================");

    $finish;
end

// Monitor task scheduling
always @(posedge clk) begin
    if(wr && CTRL_MQ_active) begin
        automatic integer laxity = task_in[31:16] - task_in[15:0];
        automatic integer threshold = task_in[15:0] + (task_in[15:0] >> 1);
        automatic string queue_type = (laxity < threshold) ? "LLF" : "SRJF";
        $display("Time=%0t: Task submitted - ID=%d, Deadline=%d, Execution=%d, Laxity=%d, Threshold=%d, Queue=%s",
                 $time, task_in[39:32], task_in[31:16], task_in[15:0],
                 laxity, threshold, queue_type);
    end
end

// Monitor laxity switches
always @(posedge CTRL_subtract) begin
    #1; // Small delay to let signals settle
    $display("Time=%0t: Laxity switches detected: %d", $time, UUT.Scheduler.SRJF_Q.IB[0].Ins_cell.subtractor.RP_LAXITY_SWITCH);
end

endmodule
