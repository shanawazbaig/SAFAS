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
// Description:     LLF Hybrid Insertion Cell with Laxity-based Priority
//                  - MODE = 0: SRJF - Compare by remaining execution time
//                  - MODE = 1: LLF - Compare by laxity (for tasks with low laxity)
//                  - Laxity = Relative_deadline - Execution_time
//                  - Low laxity threshold = 1.5 × Execution_time
// 010100101000000100011010000001010011

`timescale 1ns / 1ns
module Insertion_cell_llf #(parameter W=41, MODE=0)(
   input clk, rst,
   input subtract,
   input wr,
   input rd,
   input[W-2:0] data_in,
   input[W-1:0] data_in_pre, // data from previous cell

   output reg[W-1:0] data_reg,
   output reg[W-2:0] data_out, // replacement with oldest data_reg or send data_in.
   output reg wr_pre
    );

wire[W-1:0] data_reg_sub;

// Laxity calculation for incoming task
wire [15:0] laxity_in = data_in[31:16] - data_in[15:0];  // deadline - execution
// Threshold = 1.5 × execution time (implemented as execution + execution/2)
wire [15:0] threshold_in = data_in[15:0] + (data_in[15:0] >> 1);
wire low_laxity_in = (laxity_in < threshold_in);          // Is laxity < 1.5×execution?

// Laxity calculation for current cell task
wire [15:0] laxity_reg = data_reg[31:16] - data_reg[15:0];
wire [15:0] threshold_reg = data_reg[15:0] + (data_reg[15:0] >> 1);
wire low_laxity_reg = (laxity_reg < threshold_reg);

// Comparison logic based on MODE and laxity
wire comp;

generate
    if (MODE == 0) begin : SRJF_MODE
        // SRJF Mode: Compare by remaining execution time (shorter is higher priority)
        // For tasks with high laxity (laxity >= 1.5× execution)
        assign comp = (data_reg[15:0] <= data_in[15:0]);
    end else begin : LLF_MODE
        // LLF Mode: Compare by laxity (lower laxity is higher priority)
        // This queue handles tasks with low laxity
        assign comp = (laxity_reg <= laxity_in);
    end
endgenerate

///////////////////////////////////////////////
// SUBTRACTOR
///////////////////////////////////////////////
sub_task_llf #(.W(W), .MODE(MODE)) subtractor(
    .clk  (clk),
    .rst  (rst),
    .subtract_en(subtract),
    .RT_in (data_reg),

    .RT_out(data_reg_sub)
);

///////////////////////////////////////////////
// Cell
///////////////////////////////////////////////
always @(posedge clk or posedge rst) begin
   if(rst) begin
      data_reg    <= {1'b0, {W-1{1'b1}}};
      data_out    <= {W-1{1'b1}};
      wr_pre      <= 1'b0;
   end else begin
      if (subtract)begin
           data_reg <= data_reg_sub; // subtract
      end else begin
   ///////////////////////////////////////////
   // write and read data from insertion sort
          case ({wr, rd})
            //normal
            2'b00 : data_reg   <= data_reg;
            //read
            2'b01 : data_reg   <= data_in_pre;
            //write
            2'b10 : data_reg   <=(comp & data_reg[W-1]) ? data_reg : {1'b1, data_in};
            //read_write
            2'b11 : data_reg   <= data_in_pre;
            endcase
        end
        // outputs
        wr_pre     <= (~rd)? (wr & data_reg[W-1]) : wr_pre;
        data_out   <= (~rd & wr)? ((comp & data_reg[W-1])? data_in : data_reg[W-2:0])
                                  : data_out;
   ///////////////////////////////////////////
   end
end
endmodule

///////////////////////////////////////////////
// Subtractor with Laxity-aware priority switching
///////////////////////////////////////////////
module sub_task_llf #(parameter W=42, MODE=0)(
    input clk, rst,
    input subtract_en,
    input [(W)-1:0] RT_in,

    output reg[(W)-1:0] RT_out
   );

integer RP_MISS;
integer RP_LAXITY_SWITCH;  // Count how many tasks switch to low-laxity mode

wire check_miss = (RT_in[31:16] < RT_in[15:0]); //relative deadline < execution time

// Calculate laxity after subtraction
wire [15:0] laxity = RT_in[31:16] - RT_in[15:0];
wire [15:0] threshold = RT_in[15:0] + (RT_in[15:0] >> 1);  // 1.5 × execution time
wire low_laxity = (laxity < threshold) & (RT_in[31:16] != 0);

always @(posedge subtract_en, posedge rst) begin
  if(rst) begin
    RP_MISS = 0;
    RP_LAXITY_SWITCH = 0;
  end else if(RT_in[W-1]) begin
    RT_out[15:0]  = RT_in[15:0];
    RT_out[31:16] = (RT_in[31:16]!=0)? RT_in[31:16] - 1 : RT_in[31:16]; //deadline
    RP_MISS = (check_miss)? RP_MISS+1:RP_MISS;

    // For SRJF queue (MODE=0), mark task as critical if laxity is low
    // This will move it to the LLF queue in the next scheduling cycle
    if (MODE == 0 && low_laxity && !RT_in[40]) begin
        RT_out[40] = 1'b1;  // Mark as critical/low-laxity
        RP_LAXITY_SWITCH = RP_LAXITY_SWITCH + 1;
    end else begin
        RT_out[40] = RT_in[40];
    end

    RT_out[39:32] = RT_in[39:32];       // ID
    RT_out[W-1]   =(check_miss | RT_out[31:16]==0)? 1'b0:1'b1;
  end else RT_out = RT_in;
end

endmodule
