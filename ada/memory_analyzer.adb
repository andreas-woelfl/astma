with Text_IO;

package body Memory_Analyzer is

   function Bytes_Required (Value : in Integer) return Integer is

      Bytes_To_Long_Word : constant Integer := 4;

      Offset_To_Byte_In_Bits       : constant Integer := 8 - 1;
      Offset_To_Long_Word_In_Bytes : Integer := Bytes_To_Long_Word - 1;

   begin

      return
        ((
          (((Value + Offset_To_Byte_In_Bits) / 8) +
           Offset_To_Long_Word_In_Bytes) /
          Bytes_To_Long_Word) *
         Bytes_To_Long_Word);
   end Bytes_Required;

   function Count
     (Size : Integer;
      File : String;
      Var  : String) return Boolean
   is
   begin
      Text_IO.Put_Line
        ("local, " &
         File &
         ", " &
         Var &
         ", " &
         Integer'Image (Bytes_Required (Size)));

      return True;
   end Count;

end Memory_Analyzer;
